def write_configuration_file(config, filename):
    """
    Writes a configuration file.

    @type config: list of list.
    @param config: The configuration is a list of fields which are described
    by a list with two or three element:
       0. The field name (string);
       1. The section (string, optional);
       2. The value of the field (any type that can be converted to a string).
    @type filename: string
    @param filename: configuration-file name.
    """
    # First sorts all fields per section.
    sorted_config = {"": []}
    for field in config:
        # Determines the delimiter: semi-colon for strings, equal sign
        # for other types.
        output = field[-1]
        if isinstance(output, str):
            output = ": " + output
        else:
            output = " = " + str(output)
        output = field[0] + output
        # If no section is specified.
        if len(field) == 2:
            sorted_config[""] = output
        else:
            if field[1] in sorted_config.keys():
                sorted_config[field[1]].append(output)
            else:
                sorted_config[field[1]] = [output]

    f = open(filename, 'w')

    # Writes fields outside of sections.
    for field in sorted_config.pop(""):
        f.write(field + "\n")

    # Writes sections.
    for section in sorted_config:
        f.write("\n\n" + section + "\n\n")
        for field in sorted_config[section]:
            f.write(field + "\n")

    f.close()


def attribute_ref(path_file_in, path_file_out, Vd, Vdi, As):

    file_in = open(path_file_in, 'r')
    file_out = open(path_file_out, 'w')
    lines = file_in.readlines()
    for line in lines:
        line = line.replace('%vdiode', '%1.2e' % Vdi)
        line = line.replace('%vd', '%1.2e' % Vd)
        line = line.replace('%scav', '%1.2e' % As)
        file_out.write(line)
    file_in.close()
    file_out.close()
