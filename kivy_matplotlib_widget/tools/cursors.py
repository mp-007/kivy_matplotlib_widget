"""This file is based on mplcursors project. Some changes as been made to 
worked with kivy and my project

mplcursors project
https://github.com/anntzer/mplcursors
"""

from collections.abc import Iterable
from contextlib import suppress
import copy
import weakref
from weakref import WeakKeyDictionary

from matplotlib.axes import Axes
from matplotlib.container import Container
from matplotlib.figure import Figure

import kivy_matplotlib_widget.tools.pick_info as pick_info

def _get_rounded_intersection_area(bbox_1, bbox_2):
    """Compute the intersection area between two bboxes rounded to 8 digits."""
    # The rounding allows sorting areas without floating point issues.
    bbox = bbox_1.intersection(bbox_1, bbox_2)
    return round(bbox.width * bbox.height, 8) if bbox else 0


def _iter_axes_subartists(ax):
    r"""Yield all child `Artist`\s (*not* `Container`\s) of *ax*."""
    yield from ax.collections
    yield from ax.images
    yield from ax.lines
    yield from ax.patches
    yield from ax.texts


def _is_alive(artist):
    """Check whether *artist* is still present on its parent axes."""
    return bool(artist
                and artist.axes
                and (artist.container in artist.axes.containers
                     if isinstance(artist, pick_info.ContainerArtist) else
                     artist in _iter_axes_subartists(artist.axes)))


def _reassigned_axes_event(event, ax):
    """Reassign *event* to *ax*."""
    event = copy.copy(event)
    event.xdata, event.ydata = (
        ax.transData.inverted().transform((event.x, event.y)))
    return event


class Cursor:
    """
    A cursor for selecting Matplotlib artists.

    Attributes
    ----------
    highlight_kwargs : dict
        See the *highlight_kwargs* keyword argument to the constructor.
    """

    _keep_alive = WeakKeyDictionary()

    def __init__(self,
                 artists,
                 *,
                 multiple=False,
                 highlight=False):
        """
        Construct a cursor.

        Parameters
        ----------

        artists : List[Artist]
            A list of artists that can be selected by this cursor.

        multiple : bool, default: False
            Whether multiple artists can be "on" at the same time.  If on,
            cursor dragging is disabled (so that one does not end up with many
            cursors on top of one another).

        highlight : bool, default: False
            Whether to also highlight the selected artist.  If so,
            "highlighter" artists will be placed as the first item in the
            :attr:`extras` attribute of the `Selection`.


        """

        artists = [*artists]
        # Be careful with GC.
        self._artists = [weakref.ref(artist) for artist in artists]

        for artist in artists:
            type(self)._keep_alive.setdefault(artist, set()).add(self)

        self._multiple = multiple
        self._highlight = highlight
        self._selections=[]


    @property
    def artists(self):
        """The tuple of selectable artists."""
        # Work around matplotlib/matplotlib#6982: `cla()` does not clear
        # `.axes`.
        return tuple(filter(_is_alive, (ref() for ref in self._artists)))

    @property
    def enabled(self):
        """Whether clicks are registered for picking and unpicking events."""
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    @property
    def selections(self):
        r"""The tuple of current `Selection`\s."""
        for sel in self._selections:
            if sel.annotation.axes is None:
                raise RuntimeError("Annotation unexpectedly removed; "
                                   "use 'cursor.remove_selection' instead")
        return tuple(self._selections)

    def _get_figure(self, aoc):
        """Return the parent figure of artist-or-container *aoc*."""
        if isinstance(aoc, Container):
            try:
                ca, = {artist for artist in (ref() for ref in self._artists)
                       if isinstance(artist, pick_info.ContainerArtist)
                          and artist.container is aoc}
            except ValueError:
                raise ValueError(f"Cannot find parent figure of {aoc}")
            return ca.figure
        else:
            return aoc.figure

    def _get_axes(self, aoc):
        """Return the parent axes of artist-or-container *aoc*."""
        if isinstance(aoc, Container):
            try:
                ca, = {artist for artist in (ref() for ref in self._artists)
                       if isinstance(artist, pick_info.ContainerArtist)
                          and artist.container is aoc}
            except ValueError:
                raise ValueError(f"Cannot find parent axes of {aoc}")
            return ca.axes
        else:
            return aoc.axes

    def add_highlight(self, artist, *args, **kwargs):
        """
        Create, add, and return a highlighting artist.

        This method is should be called with an "unpacked" `Selection`,
        possibly with some fields set to None.

        It is up to the caller to register the artist with the proper
        `Selection` (by calling ``sel.extras.append`` on the result of this
        method) in order to ensure cleanup upon deselection.
        """
        hl = pick_info.make_highlight(
            artist, *args,
            **{"highlight_kwargs": self.highlight_kwargs, **kwargs})
        if hl:
            artist.axes.add_artist(hl)
            return hl

    # def _on_select_event(self, event):
        
        
    #     if (not self._filter_mouse_event(event)
    #             # See _on_pick.  (We only suppress selects, not deselects.)
    #             or event in self._suppressed_events):
    #         return
    #     # Work around lack of support for twinned axes.
    #     per_axes_event = {ax: _reassigned_axes_event(event, ax)
    #                       for ax in {artist.axes for artist in self.artists}}
    #     pis = []
    #     for artist in self.artists:
    #         if (artist.axes is None  # Removed or figure-level artist.
    #                 or event.canvas is not artist.figure.canvas
    #                 or not artist.get_visible()
    #                 or not artist.axes.contains(event)[0]):  # Cropped by axes.
    #             continue
    #         pi = pick_info.compute_pick(artist, per_axes_event[artist.axes])
    #         if pi:
    #             pis.append(pi)
    #     # The any() check avoids picking an already selected artist at the same
    #     # point, as likely the user is just dragging it.  We check this here
    #     # rather than not adding the pick_info to pis at all, because in
    #     # transient hover mode, selections should be cleared out only when no
    #     # candidate picks (including such duplicates) exist at all.
    #     pi = min((pi for pi in pis
    #               if not any((pi.artist, tuple(pi.target))
    #                          == (other.artist, tuple(other.target))
    #                          for other in self._selections)),
    #              key=lambda pi: pi.dist, default=None)
    #     if pi:
    #         #do kivy stuuf
    #         # self.add_selection(pi)
    #         pass

    def xy_event(self, event):
        
        # Work around lack of support for twinned axes.
        per_axes_event = {ax: _reassigned_axes_event(event, ax)
                          for ax in {artist.axes for artist in self.artists}}
        pis = []
        for artist in self.artists:
            if (artist.axes is None  # Removed or figure-level artist.
                    or not artist.get_visible()):
                continue
            pi = pick_info.compute_pick(artist, per_axes_event[artist.axes])
            if pi:
                pis.append(pi)
        # The any() check avoids picking an already selected artist at the same
        # point, as likely the user is just dragging it.  We check this here
        # rather than not adding the pick_info to pis at all, because in
        # transient hover mode, selections should be cleared out only when no
        # candidate picks (including such duplicates) exist at all.
        pi = min((pi for pi in pis
                  if not any((pi.artist, tuple(pi.target))
                             == (other.artist, tuple(other.target))
                             for other in self._selections)),
                 key=lambda pi: pi.dist, default=None)
            
        if pi:
            if event.compare_xdata:
                min_distance=pi.dist
                # print(pi)
                pi_list=[]
                for pi in pis:
                    if not any((pi.artist, tuple(pi.target))
                               == (other.artist, tuple(other.target))
                               for other in self._selections):
                        if pi.dist==min_distance:
                            pi_list.append(pi)
                return pi_list

            #do kivy stuff
            # self.add_selection(pi)
            return pi


def cursor(pltfig,pickables=None,remove_artists=[], **kwargs):
    """
    Create a `Cursor` for a list of artists, containers, and axes.

    Parameters
    ----------

    pltfig: matplotlib figure object
    pickables : Optional[List[Union[Artist, Container, Axes, Figure]]]
        All artists and containers in the list or on any of the axes or
        figures passed in the list are selectable by the constructed `Cursor`.
        Defaults to all artists and containers on any of the figures that
        :mod:`~matplotlib.pyplot` is tracking.  Note that the latter will only
        work when relying on pyplot, not when figures are directly instantiated
        (e.g., when manually embedding Matplotlib in a GUI toolkit).

    **kwargs
        Keyword arguments are passed to the `Cursor` constructor.
    """

    # Explicit check to avoid a confusing
    # "TypeError: Cursor.__init__() got multiple values for argument 'artists'"
    if "artists" in kwargs:
        raise TypeError(
            "cursor() got an unexpected keyword argument 'artists'")

    if pickables is None:
        pickables = [pltfig]
    elif (isinstance(pickables, Container)
          or not isinstance(pickables, Iterable)):
        pickables = [pickables]

    def iter_unpack_figures(pickables):
        for entry in pickables:
            if isinstance(entry, Figure):
                yield from entry.axes
            else:
                yield entry

    def iter_unpack_axes(pickables):
        for entry in pickables:
            if isinstance(entry, Axes):
                yield from _iter_axes_subartists(entry)
                containers.extend(entry.containers)
            elif isinstance(entry, Container):
                containers.append(entry)
            else:
                yield entry

    containers = []
    artists = [*iter_unpack_axes(iter_unpack_figures(pickables))]
    for container in containers:
        contained = [*filter(None, container.get_children())]
        for artist in contained:
            with suppress(ValueError):
                artists.remove(artist)
        if contained:
            artists.append(pick_info.ContainerArtist(container))

    if remove_artists:
        for current_artist in remove_artists:
            if current_artist in artists:
                artists.remove(current_artist)

    return Cursor(artists, **kwargs)
