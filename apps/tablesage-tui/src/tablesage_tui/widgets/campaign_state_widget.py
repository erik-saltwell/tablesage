# from typing import Any

# from rich.text import Text
# from textual.events import Click
# from textual.message import Message
# from textual.widget import Widget

# UNSTARTED_COLOR = "#d8b06a"
# ACTIVE_COLOR = "#6f8a5a"
# ARCHIVED_COLOR = "#8a5a5a"

# _STATE_ORDER = (CampaignState.Active, CampaignState.Unstarted, CampaignState.Archived)
# _STATE_COLORS = {
#     CampaignState.Unstarted: UNSTARTED_COLOR,
#     CampaignState.Active: ACTIVE_COLOR,
#     CampaignState.Archived: ARCHIVED_COLOR,
# }


# class CampaignStateWidget(Widget):
#     DEFAULT_CSS = """
#     CampaignStateWidget {
#         height: 1;
#     }
#     """

#     class StateChanged(Message):
#         def __init__(self, state: CampaignState) -> None:
#             super().__init__()
#             self.state = state

#     def __init__(self, state: CampaignState, **kwargs: Any) -> None:
#         super().__init__(**kwargs)
#         self._state = state

#     def render(self) -> Text:
#         content = Text()
#         for state in _STATE_ORDER:
#             circle = "● " if state == self._state else "○ "
#             content.append(circle, style=_STATE_COLORS[state])
#         content.append(str(self._state), style=_STATE_COLORS[self._state])
#         return content

#     def on_click(self, event: Click) -> None:
#         circle_index = event.offset.x // 2
#         if 0 <= circle_index < len(_STATE_ORDER):
#             new_state = _STATE_ORDER[circle_index]
#             if new_state != self._state:
#                 self._state = new_state
#                 self.refresh()
#                 self.post_message(self.StateChanged(new_state))
