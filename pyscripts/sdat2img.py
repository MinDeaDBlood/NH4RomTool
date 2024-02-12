import errno
import os


class sdat2img:
    def __init__(self, TRANSFER_LIST_FILE, NEW_DATA_FILE, OUTPUT_IMAGE_FILE):
        print('sdat2img binary - version: 1.3\n')
        self.TRANSFER_LIST_FILE = TRANSFER_LIST_FILE
        self.NEW_DATA_FILE = NEW_DATA_FILE
        self.OUTPUT_IMAGE_FILE = OUTPUT_IMAGE_FILE
        self.list_file = self.parse_transfer_list_file()
        block_size = 4096
        version = next(self.list_file)
        self.version = str(version)
        next(self.list_file)
        show = "Android {} detected!\n"
        if version == 1:
            print(show.format("Lollipop 5.0"))
        elif version == 2:
            print(show.format("Lollipop 5.1"))
        elif version == 3:
            print(show.format("Marshmallow 6.x"))
        elif version == 4:
            print(show.format("Nougat 7.x / Oreo 8.x / Pie 9.x"))
        else:
            print(show.format('Unknown Android version {version}!\n'))

        # Don't clobber existing files to avoid accidental data loss
        try:
            output_img = open(self.OUTPUT_IMAGE_FILE, 'wb')
        except IOError as e:
            if e.errno == errno.EEXIST:
                print('Error: the output file "{}" already exists'.format(e.filename))
                print('Remove it, rename it, or choose a different file name.')
                return
            else:
                raise

        new_data_file = open(self.NEW_DATA_FILE, 'rb')
        max_file_size = 0

        for command in self.list_file:
            max_file_size = max(pair[1] for pair in [i for i in command[1]]) * block_size
            if command[0] == 'new':
                for block in command[1]:
                    begin = block[0]
                    block_count = block[1] - begin
                    print('\rCopying {} blocks into position {}...'.format(block_count, begin), end="")

                    # Position output file
                    output_img.seek(begin * block_size)

                    # Copy one block at a time
                    while block_count > 0:
                        output_img.write(new_data_file.read(block_size))
                        block_count -= 1
            else:
                print('\rSkipping command {}...'.format(command[0]), end="")

        # Make file larger if necessary
        if output_img.tell() < max_file_size:
            output_img.truncate(max_file_size)

        output_img.close()
        new_data_file.close()
        print('\nDone! Output image: {}'.format(os.path.realpath(output_img.name)))

    @staticmethod
    def rangeset(src):
        src_set = src.split(',')
        num_set = [int(item) for item in src_set]
        if len(num_set) != num_set[0] + 1:
            print('Error on parsing following data to rangeset:\n{}'.format(src))
            return

        return tuple([(num_set[i], num_set[i + 1]) for i in range(1, len(num_set), 2)])

    def parse_transfer_list_file(self):
        with open(self.TRANSFER_LIST_FILE, 'r') as trans_list:
            # First line in transfer list is the version number
            # Second line in transfer list is the total number of blocks we expect to write
            if (version := int(trans_list.readline())) >= 2 and (new_blocks := int(trans_list.readline())):
                # Third line is how many stash entries are needed simultaneously
                trans_list.readline()
                # Fourth line is the maximum number of blocks that will be stashed simultaneously
                trans_list.readline()
            # Subsequent lines are all individual transfer commands
            yield version
            yield new_blocks
            for line in trans_list:
                line = line.split(' ')
                cmd = line[0]
                if cmd in ['erase', 'new', 'zero']:
                    yield [cmd, self.rangeset(line[1])]
                else:
                    # Skip lines starting with numbers, they are not commands anyway
                    if not cmd[0].isdigit():
                        print('Command "{}" is not valid.'.format(cmd))
                        return
