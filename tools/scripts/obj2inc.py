from optparse import OptionParser


platforms = ["X86", "X64", "ARM", "ARM64"]

def _read_line(process_list, lineno):
    try:
        return process_list[lineno].strip()
    except IndexError:
        raise SyntaxError("syntax error in line %d" %lineno)

def obj2inc(in_file, platforms):
    # create obj dict
    obj_dict = {}
    for platform in platforms:
        obj_dict[platform] = []

    in_data = in_file.read().splitlines()
    out = "{This file is autogenerated. Don't edit it!}\n\n"
    lineno = 0

    # process file
    while True:
        # break if end of list
        try:
            line = _read_line(in_data, lineno)
            lineno += 1
        except SyntaxError:
            break

        # skip comments and empty strings
        if line.startswith("#") or not line:
            continue

        # find tag with the archiver name 
        if line.startswith("["):
            archiver = line[1: line.find("]")].upper()
            line = _read_line(in_data, lineno)

            # fill object dict
            while line.upper() != "[/%s]" %archiver:
                # skip comments and empty strings
                if line.startswith("#") or not line:
                    pass
                else:
                    for platform in platforms:
                        obj_dict[platform].append((archiver, line))
                lineno += 1; line = _read_line(in_data, lineno)

            lineno += 1

    # create out
    for platform in platforms:
        out += "{$ifdef CPU%s}\n" %platform
        for obj in obj_dict[platform]:
            out += "  {$L '%s/%s/%s'}\n" %(platform.lower(), obj[0], obj[1])
        out += "{$endif}\n\n"

    return out


if __name__ == "__main__":


    parser = OptionParser()
    parser.add_option("-p", "--project", dest="project_name",
                      help="project name")
    parser.add_option("-f", "--file", dest="file_path",
                      help="path to the file with list processing objs")
    (options, args) = parser.parse_args()

    try:
        in_file = open(options.file_path)
    except IOError:
        raise IOError("no such file: %s" %options.file_path)

    try:
        out_file = open("./%s_objs.inc" %options.project_name, "w")
    except IOError:
        raise IOError("can't create file: %s" %options.file_path)

    print "Processing..."

    out = obj2inc(in_file, platforms)
    out_file.write(out)
    out_file.close()

    print "Done."
    