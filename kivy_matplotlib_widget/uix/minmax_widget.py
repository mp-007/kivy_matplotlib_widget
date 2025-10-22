from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput

from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    StringProperty,
    BooleanProperty,
    ColorProperty,
    DictProperty,
)

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core import text as coretext


def add_minmax(
    figure_wgt,
    xaxis_formatter=None,
    invert_xaxis_formatter=None,
    yaxis_formatter=None,
    invert_yaxis_formatter=None,
):

    if hasattr(figure_wgt, "text_instance"):
        if figure_wgt.text_instance is None:
            text_widget = TextBox()
        else:
            text_widget = figure_wgt.text_instance

        text_widget.figure_wgt = figure_wgt
        text_widget.xaxis_formatter = xaxis_formatter
        text_widget.invert_xaxis_formatter = invert_xaxis_formatter
        text_widget.yaxis_formatter = yaxis_formatter
        text_widget.invert_yaxis_formatter = invert_yaxis_formatter

        text_widget.x_text_pos = figure_wgt.x
        text_widget.y_text_pos = figure_wgt.y

        if figure_wgt.text_instance is None:
            figure_wgt.parent.add_widget(text_widget)
        figure_wgt.text_instance = text_widget


class BaseTextFloatLayout(FloatLayout):
    """Touch egend kivy class"""

    figure_wgt = ObjectProperty(None)
    current_axis = ObjectProperty(None)
    kind = DictProperty({"axis": "x", "anchor": "right"})
    x_text_pos = NumericProperty(10)
    y_text_pos = NumericProperty(10)
    show_text = BooleanProperty(False)

    def __init__(self, **kwargs):
        """init class"""
        super().__init__(**kwargs)

    def reset_text(self):
        """reset text attribute"""
        self.x_text_pos = 1
        self.y_text_pos = 1


class TextBox(BaseTextFloatLayout):
    """text box widget"""

    text_color = ColorProperty([0, 0, 0, 1])
    text_font = StringProperty("Roboto")
    text_size = NumericProperty(dp(14))
    background_color = ColorProperty([1, 1, 1, 0.9])
    text_height = NumericProperty(dp(36))
    text_width = NumericProperty(dp(40))
    offset_text = BooleanProperty(False)
    xaxis_formatter = None
    invert_xaxis_formatter = None
    yaxis_formatter = None
    invert_yaxis_formatter = None
    current_text = ""

    def __init__(self, **kwargs):
        """init class"""
        super().__init__(**kwargs)

    def on_axis_validation(self, instance) -> bool:
        """Called to validate axis value.

        Args:
            instance (widget) : kivy widget object

        Returns:
            bool: if the value is valid or not.
        """

        if not instance.text:
            return False

        try:
            if self.kind.get("axis") == "x" and self.invert_xaxis_formatter:
                number = float(self.invert_xaxis_formatter(instance.text))
            elif self.kind.get("axis") == "y" and self.invert_yaxis_formatter:
                number = float(self.invert_yaxis_formatter(instance.text))
            else:
                number = float(instance.text)
        except ValueError:
            return False
        return True

    def on_set_axis(self, instance):
        """On set axis (in textinput), validate the input

        Args:
            instance (widget) : kivy widget object

        """
        if (
            not instance.focused
            and self.on_axis_validation(instance)
            and self.current_text != instance.text
        ):

            kind = self.kind
            if self.kind.get("axis") == "x" and self.invert_xaxis_formatter:
                number = float(self.invert_xaxis_formatter(instance.text))
            elif self.kind.get("axis") == "y" and self.invert_yaxis_formatter:
                number = float(self.invert_yaxis_formatter(instance.text))
            else:
                number = float(instance.text)

            if kind.get("axis") == "x":
                if kind.get("anchor") == "left":
                    self.current_axis.set_xlim((number, None))

                elif kind.get("anchor") == "right":
                    self.current_axis.set_xlim((None, number))
            elif kind.get("axis") == "y":
                if kind.get("anchor") == "bottom":
                    self.current_axis.set_ylim((number, None))

                elif kind.get("anchor") == "top":
                    self.current_axis.set_ylim((None, number))
            self.current_axis.figure.canvas.draw_idle()
            self.current_axis.figure.canvas.flush_events()

            self.show_text = False

    def autofocus_text(self, *args) -> None:
        """auto focus text input

        Returns:
            None
        """
        Clock.schedule_once(self.scheduled_autofocus_text, 0.2)

    def scheduled_autofocus_text(self, *args):
        self.ids.text_input.focus = True
        Clock.schedule_once(self.select_all_text, 0.2)

    def select_all_text(self, *args):
        self.ids.text_input.select_all()

    def on_show_text(self, instance, val):
        if val:
            kind = self.kind

            if kind.get("axis") == "x":
                xlim = self.current_axis.get_xlim()
                if self.xaxis_formatter is None:
                    axis_formatter = (
                        self.current_axis.fmt_xdata
                        if self.current_axis.fmt_xdata is not None
                        else self.current_axis.xaxis.get_major_formatter().format_data_short
                    )
                else:
                    axis_formatter = self.xaxis_formatter

                if kind.get("anchor") == "left":
                    # u"\u2212" is to manage unicode minus
                    self.ids.text_input.text = f"{
                        axis_formatter(
                            xlim[0])}".replace(
                        "\u2212", "-"
                    )

                elif kind.get("anchor") == "right":
                    # u"\u2212" is to manage unicode minus
                    self.ids.text_input.text = f"{
                        axis_formatter(
                            xlim[1])}".replace(
                        "\u2212", "-"
                    )
                self.current_value = self.ids.text_input.text

            elif kind.get("axis") == "y":
                ylim = self.current_axis.get_ylim()
                if self.yaxis_formatter is None:
                    axis_formatter = (
                        self.current_axis.fmt_ydata
                        if self.current_axis.fmt_ydata is not None
                        else self.current_axis.yaxis.get_major_formatter().format_data_short
                    )
                else:
                    axis_formatter = self.xaxis_formatter
                if kind.get("anchor") == "bottom":
                    # u"\u2212" is to manage unicode minus
                    self.ids.text_input.text = f"{
                        axis_formatter(
                            ylim[0])}".replace(
                        "\u2212", "-"
                    )

                elif kind.get("anchor") == "top":
                    # u"\u2212" is to manage unicode minus
                    self.ids.text_input.text = f"{
                        axis_formatter(
                            ylim[1])}".replace(
                        "\u2212", "-"
                    )
                self.current_value = self.ids.text_input.text
            self.autofocus_text()


class CustomTextInput(TextInput):
    """Variation of kivy TextInput"""

    text_width = NumericProperty(100)

    """The text width
    """

    text_box_instance = figure_wgt = ObjectProperty(None)
    textcenter = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super(CustomTextInput, self).__init__(*args, **kwargs)
        self.bind(focus=self.on_focus_text)

    def update_textbox(self, *args):
        """
        Update the text box from text width
        """

        if self.text:

            try:
                string = self.text
                text_texture_width = coretext.Label(
                    font_size=self.font_size
                ).get_extents(string)[0]

            except BaseException:
                print("get text width failed")
            else:
                if self.text_box_instance:
                    if text_texture_width > dp(20):
                        self.text_box_instance.text_width = (
                            text_texture_width
                            + self.padding[0]
                            + self.padding[2]
                        )
                    else:
                        self.text_box_instance.text_width = (
                            dp(20) + self.padding[0] + self.padding[2]
                        )

    def on_focus_text(self, instance, value):
        """on focus operation"""
        if value:
            # User focused
            pass
        else:
            # User defocused
            self.text_box_instance.show_text = False


Builder.load_string(
    """

<BaseTextFloatLayout>
    size_hint: None,None
    width: dp(0.01)
    height: dp(0.01)
    opacity:1 if root.show_text else 0

<TextBox>
    BoxLayout:
        x:
            root.x_text_pos - root.text_width + dp(20) if root.offset_text else root.x_text_pos
        y:
            root.y_text_pos - dp(3)
        size_hint: None, None
        height: root.text_height
        width:
            root.text_width if root.show_text \
            else dp(0.0001)

        canvas:
            Color:
                rgba: root.background_color
            Rectangle:
                pos: self.pos
                size: self.size
        CustomTextInput:
            id:text_input
            text_box_instance:root
            font_size:root.text_size
            color: root.text_color
            font_name : root.text_font
            last_good_entry:None
            on_text_validate:
                root.on_axis_validation(self)
            on_focus:
                root.on_set_axis(self)

<CustomTextInput>
    foreground_color: (0,0,0,1)
    background_color: (0,0,0,0)
    font_size:dp(14)
    on_text: root.update_textbox()
    multiline:False
        """
)
