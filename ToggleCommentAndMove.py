import sublime
import sublime_plugin
import re

def GetCommentSymbol(cmd_ctx):
    # self.view.meta_info('block_comment', 0)
    syntax_symbols = cmd_ctx.view.meta_info('shellVariables', 0)

    # {'value': '#', name: 'TM_COMMENT_START'}
    for symbol_entry in syntax_symbols:
        symbol, name = symbol_entry.values()
        if name == 'TM_COMMENT_START':
            return symbol


# get regions that have cursors on them
# [(line_char_start, line_char_end), ...]
def get_lines_with_selections(view) -> list:
    selections = view.sel()

    line_regions = []

    for selection in selections:
        lines_in_sel = view.lines(selection)
        for region in lines_in_sel:
            line_regions.append( region )

    return line_regions


def get_soft_start_offset(line_text):
    """
    soft line start (if line isn't empty),
    0 if the line is empty
    """
    whitespace = re.compile(r'(\s|\t)+')
    match = re.match(whitespace, line_text)

    if match:
        return match.end()

    return 0


def string_at(needle, haystack, start_pos) -> bool:
    return haystack[start_pos:start_pos+len(needle)] == needle


# returns the new state,
# True for commented, False for uncommented
def toggle_line_comment(view, edit, line_region, comment_pattern) -> bool:
    line_text = view.substr( line_region )

    soft_start_pos = get_soft_start_offset(line_text)
    is_comment = string_at(comment_pattern, line_text, soft_start_pos)
    comment_pos = line_region.begin()+soft_start_pos

    comment_len = len(comment_pattern)

    if not is_comment: # line was comment
        view.insert(edit, comment_pos, comment_pattern)
    else: # erase comment
        comment_region = sublime.Region(comment_pos, comment_pos+comment_len)
        view.erase(edit, comment_region)


def toggle_line_comments(view, edit, line_regions, comment_pattern):
    shift_lines_by = 0 # for shifting line regions when erasing/adding comments

    for line_region in line_regions:
        line_region = sublime.Region( line_region.begin()+shift_lines_by, line_region.end()+shift_lines_by) # update line region to match
        commented = toggle_line_comment(view, edit, line_region, comment_pattern)
        if commented:
            shift_lines_by += 3
        else:
            shift_lines_by -= 3


def toggle_comment_fallback(view, cmd_edit, comment_pattern):
    lines_with_cursors = get_lines_with_selections(view)
    view.run_command("move", {"by": "lines", "forward": True})

    toggle_line_comments(view, cmd_edit, lines_with_cursors, comment_pattern)


class ToggleCommentAndMoveCommand(sublime_plugin.TextCommand):

    def run(self, edit, forward=True, move=True, fallback_uses_space=True):
        comment_symbol = GetCommentSymbol(self)
        symbol_missing = (comment_symbol == None)
        comment_symbol = comment_symbol or "//"

        if fallback_uses_space:
            comment_symbol += " "

        if symbol_missing:
            toggle_comment_fallback(self.view, edit, comment_symbol)
        else:
            self.view.run_command("toggle_comment", {"block": False})

        # if move:
            # self.view.run_command("move", {"by": "lines", "forward": forward})


