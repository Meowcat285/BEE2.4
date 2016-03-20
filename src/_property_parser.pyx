# cython: language_level=3
from property_parser import KeyValError, NoKeyError
import utils

cdef extern from "Python.h":
    # Directly use some Cpython API bits, where we know it's the base type

    # list.append()
    int PyList_Append(object list, object x) except -1

    # bytes.decode()..
    str PyUnicode_FromEncodedObject(object obj, const char *encoding, const char *errors)

cdef is_identifier(obj_value):
    value = <str>obj_value
    for bad_char in '"{}[]':
        if bad_char in value:
            return False
    return True

cdef str read_multiline_value(file, line_num, filename):
    """Pull lines out until a quote character is reached."""
    lines = ['']  # We return with a beginning newline
    cdef basestring line
    # Re-looping over the same iterator means we don't repeat lines
    for line_num, line in file:
        if isinstance(line, bytes):
            # Decode bytes using utf-8
            line = PyUnicode_FromEncodedObject(line, 'utf-8', NULL)
        line = line.strip()
        if line[-1:] == '"':
            PyList_Append(lines, line[:-1])
            return '\n'.join(lines)
        PyList_Append(lines, line)
    else:
        # We hit EOF!
        raise KeyValError(
            "Reached EOF without ending quote!",
            filename,
            line_num,
        )


cdef int read_flag(line_end, filename, line_num) except -1:
    """Read a potential [] flag."""
    cdef str flag, comment
    cdef bint inv

    flag = line_end.lstrip()
    if flag[:1] == '[':
        if ']' not in flag:
            raise KeyValError(
                'Unterminated [flag] on '
                'line: "{}"'.format(line_end),
                filename,
                line_num,
            )
        flag, comment = flag.split(']', 1)
        # Parse the flag
        if flag[:1] == '!':
            inv = True
            flag = flag[1:]
        else:
            inv = False
    else:
        comment = flag
        flag = inv = None

    # Check for unexpected text at the end of a line..
    comment = comment.lstrip()
    if comment and comment[:2] != '//':
        raise KeyValError(
            'Extra text after '
            'line: "{}"'.format(line_end),
            filename,
            line_num,
        )

    if flag:
        # If inv is False, we need True flags.
        # If inv is True, we need False flags.
        return inv != get_flag(flag)
    return 1

cdef int get_flag(str flag_name) except -1:
    cdef str flag = flag_name.casefold()

    if flag in ('x360', 'ps3', 'gameconsole'):
        return False
    elif flag == 'win32':  # Not actually windows, it actually means 'PC'
        return True
    elif flag == 'osx':
        return utils.MAC
    elif flag == 'linux':
        return utils.LINUX
    else:
        return True # Assume it passed


def property_parse(object file_contents, str filename=''):
    """Returns a Property tree parsed from given text.

    filename, if set should be the source of the text for debug purposes.
    file_contents should be an iterable of strings
    """
    from property_parser import Property
    cdef list open_properties, cur_block, line_contents
    cdef str freshline

    cdef object file_iter = enumerate(file_contents, 1)

    # The block we are currently adding to.
    cur_block = []

    # The special name 'None' marks it as the root property, which
    # just outputs its children when exported. This way we can handle
    # multiple root blocks in the file, while still returning a single
    # Property object which has all the methods.

    # A queue of the properties we are currently in (outside to inside).
    open_properties = [Property(None, cur_block)]

    # Do we require a block to be opened next? ("name"\n must have { next.)
    cdef bint requires_block = False
    cdef int line_num

    for line_num, line in file_iter:
        if isinstance(line, bytes):
            # Decode bytes using utf-8
            line = PyUnicode_FromEncodedObject(line, 'utf-8', NULL)
        line = <str>line

        freshline = line.strip()

        if not freshline or freshline[:2] == '//':
            # Skip blank lines and comments!
            continue

        if freshline[0] == '"':   # data string
            line_contents = freshline.split('"')
            name = line_contents[1]
            if len(line_contents) > 3:
                value = line_contents[3]
            else:  # It doesn't have a value - it's a block.
                PyList_Append(cur_block, Property(name, ''))
                requires_block = True  # Ensure the next token must be a '{'.
                continue  # Ensure we skip the check for the above value

            # Special case - comment between name/value sections -
            # it's a name block then.
            if line_contents[2].lstrip()[:2] == '//':
                PyList_Append(cur_block, Property(name, ''))
                requires_block = True
                continue
            else:
                if len(line_contents) < 5:
                    # It's a multiline value - no ending quote!
                    value += read_multiline_value(
                        file_iter,
                        line_num,
                        filename,
                    )
                value = value.replace(r'\n', '\n').replace(r'\t', '\t')
                value = value.replace('\\\\', '\\').replace('\/', '/')

            # Line_contents[4] is the start of the comment, check for [] flags.
            if len(line_contents) >= 5:
                if read_flag(line_contents[4], filename, line_num):
                    PyList_Append(cur_block, Property(name, value))
            else:
                # No flag, add unconditionally
                PyList_Append(cur_block, Property(name, value))

        elif freshline[0] == '{':
            # Open a new block - make sure the last token was a name..
            if not requires_block:
                raise KeyValError(
                    'Property cannot have sub-section if it already '
                    'has an in-line value.',
                    filename,
                    line_num,
                )
            requires_block = False
            PyList_Append(open_properties, cur_block[-1])
            cur_block[-1].value = cur_block = []

        elif freshline[0] == '}':
            # Move back a block
            cur_block = open_properties.pop().value
            if len(open_properties) == 0:
                # No open blocks!
                raise KeyValError(
                    'Too many closing brackets.',
                    filename,
                    line_num,
                )

        # Handle name bare on one line - it's a name block. This is used
        # in VMF files...
        elif is_identifier(freshline):
            PyList_Append(cur_block, Property(freshline, ''))
            requires_block = True
            continue
        else:
            raise KeyValError(
                "Unexpected beginning character '"
                + freshline[0]
                + '"!',
                filename,
                line_num,
            )

        # A "name" line was found, but it wasn't followed by '{'!
        if requires_block:
            raise KeyValError(
                "Block opening ('{') required!",
                filename,
                line_num,
            )

    if len(open_properties) > 1:
        raise KeyValError(
            'End of text reached with remaining open sections.',
            filename,
            line=None,
        )
    return open_properties[0]