__author__ = 'Sergey Alyaev'

"""Collect command-line options in a dictionary"""


def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts



class bibentry(object):

    #staic
    label_to_abbrev = dict()
    abbreviations = set()

    def __init__(self, entry_type, entry_label = None):
        self.entry_type = entry_type
        self.entry_label = entry_label
        self.fields = dict()
        self.abbr = None

    def __str__(self):
        return self.entry_label + ":[" + self.entry_type + "]"

    def __repr__(self):
        return self.__str__()

    def strip_author_name(self, author_name, abbreviate=True):
        """
        Makes name to desired format
        :param author_name:
        :param abbreviate:
        :return:
        """
        if abbreviate:
            name_parts = author_name.split(',')
            out = name_parts[0].strip()
            if len(name_parts)>1:
                out += '~'
                name_parts = name_parts[1].split(' ')
                for i in range(len(name_parts)):
                    if len(name_parts[i].strip())>0:
                        out += name_parts[i].strip()[0]+'.'
            return out
        else:
            return author_name.strip()




    def get_authors(self, max_authors=3, abbreviate=True):
        """

        :param max_authors:
        :return:
        """
        out = ""
        if 'author' in self.fields:
            authors = self.fields['author'].split(' and ')
            total_len = len(authors)
            if total_len <= 1:
                out += self.strip_author_name(authors[0], abbreviate)
            elif (total_len > max_authors+1):
                for i in range(max_authors-1):
                    out += self.strip_author_name(authors[i], abbreviate)+", "
                out += self.strip_author_name(authors[max_authors-1], abbreviate)+" et~al."
            else:
                for i in range(total_len-1):
                    out += self.strip_author_name(authors[i], abbreviate)+", "
                out += "and " + self.strip_author_name(authors[total_len-1], abbreviate)
        else:
            out = 'x'
        return out


    def get_year(self):
        """

        :return:
        """
        out = ''
        if 'year' in self.fields:
            out += (self.fields['year'].strip())
        return out

    def get_title(self):
        """

        :return:
        """
        out = ''
        if 'title' in self.fields:
            out += (self.fields['title'].strip())
        return out

    url_prefix = 'URL '
    doi_prefix = 'http://dx.doi.org/'

    def get_url(self, url_enviorment, prefer_doi = True):
        """

        :return:
        """
        out = ''
        added = False
        if 'url' in self.fields:
            out = self.url_prefix + url_enviorment+'{'+ self.fields['url']+'}'
            added = True
        if 'doi' in self.fields:
            if (not added) or prefer_doi:
                out = self.url_prefix + url_enviorment+'{'+self.doi_prefix+self.fields['doi'] +'}'
        return out


    def get_publisher(self, always_with_publisher=False):
        """
        gets the publisher e.g. journal
        :return:
        """
        out = ''
        if self.entry_type.lower().find('mastersthesis')>=0:
            out += 'Master\'s thesis. '
            if 'school' in self.fields:
                out += self.fields['school']
        elif self.entry_type.lower().find('phdthesis')>=0:
            out += 'PhD thesis. '
            if 'school' in self.fields:
                out += self.fields['school']
        elif 'journal' in self.fields:
            if self.entry_type.lower() == 'unpublished':
                out += "submitted to "
            out += self.fields['journal']
        elif 'booktitle' in self.fields:
            out += 'in '+ self.fields['booktitle']
        elif 'note' in self.fields:
            out += self.fields['note']

        if always_with_publisher or len(out)==0:
            if 'publisher' in self.fields:
                out += ' (' + self.fields['publisher']+')'
            elif 'organization' in self.fields:
                out += ' (' + self.fields['organization']+')'

        if (len(out)>0):
            return out+'.'
        else:
            return ''

    def get_abbreviation(self):
        """
        :return abbreviation
        """
        #TODO test for multiple of the same to work correctly
        if self.label_to_abbrev.has_key(self.entry_label):
            return self.label_to_abbrev[self.entry_label]
        abbr = ''
        if 'author' in self.fields:
            authors = self.fields['author'].split(' and ')
            for a in authors:
                abbr += a[0]
        else:
            abbr = 'x'
        if 'year' in self.fields:
            abbr += self.fields['year']
        if abbr in self.abbreviations:
            abbr += 'a'
        while abbr in self.abbreviations:
            abbr[len(abbr)] = chr(int(abbr[len(abbr)])+1)
        self.label_to_abbrev[self.entry_label] = abbr
        self.abbreviations.add(abbr)
        return abbr






def find_first_outer_brackets(st):
    """
    :param st:
    :return: finds closing "{}" paranthesis non-matching
    """
    opened = 0
    open_b = -1
    index = 0
    while index < len(st):
        c = st[index]
        if (c == '{'):
            opened +=1
            if open_b == -1:
                open_b = index
        if (c == '}'):
            opened -=1
            if opened == 0:
                close_b = index
                return open_b, close_b
        if (c == '\\'):
            index += 1
        if opened < 0:
            print("Incorrect parenthesis in ", st)
            return -1, -1
        index+=1
    print("No bracket pairs found ", st)
    return -1, -1

def populate_entry(entry, st):
    clean = st.strip()
    comma_pos = clean.find(',')
    entry.entry_label = clean[0:comma_pos]
    while True:
        clean = clean[comma_pos+1:].strip()
        p_in, p_out = find_first_outer_brackets(clean)
        if (p_in<0 or p_out<0):
            break
        eq_ind = clean.find('=', 0, p_in)
        key = clean[0:eq_ind].strip()
        value = clean[p_in+1:p_out].strip()
        entry.fields[key] = value
        comma_pos = clean.find(',', p_out)
        if comma_pos < 0:
            break


def check_person(entry, person):
    """
    checks if the person is the author of the entry
    :param entry:
    :param person:
    :return:
    """
    if person == None:
        return True
    if 'author' in entry.fields:
        if entry.fields['author'].find(person) >= 0:
            return True
    return False


def find_entries(st, person_name = None):
    entries = []
    while True:
        index = st.find('@')
        if index==-1:
            break
        st = st[index:]
        b_in, b_out = find_first_outer_brackets(st)

        #print(st[b_in+1:b_out  ])
        entry = bibentry(st[1:b_in])
        populate_entry(entry, st[b_in+1:b_out])
        if check_person(entry, person_name):
            entries.append(entry)
        st = st[b_out+1:]

    return  entries


def parse_bib_file(filename, person_name):
    file = open(filename, 'r')
    lines = file.readlines()
    st = ''
    for line in lines:
        st += line
    file.close()
    return find_entries(st, person_name)


def get_sorting(entry):
    """

    :param entry: bib entry
    :return: gets 'year'
    """
    if 'year' in entry.fields:
        if 'author' in entry.fields:
            return entry.fields['year'], entry.fields['author']
        else:
            return entry.fields['year'], "ZZZ"
    else:
        return '0000', "ZZZ"

def get_year(entry):
    """

    :param entry: bib entry
    :return: gets 'year'
    """
    if 'year' in entry.fields:
        return entry.fields['year']
    else:
        return '0000'




# "\\providecommand{\\url}[1]{\\texttt{#1}}\n" \
file_prefix =               "\\providecommand{\\urlprefix}{URL }\n"
file_suffix = "\n"

def entry_to_tex(entry):
    """

    :param entry:
    :return:
    """
    s = '\\paperecvitem{'
    s += "\\label{" + entry.entry_label + "}"
    s += entry.get_authors()
    s += " ("+entry.get_year()+")"
    s += "}"
    s += "{"
    s += "\\highlight{"
    s += entry.get_title()
    s += ",} "
    s += entry.get_publisher(False) +' '
    s += entry.get_url(url_enviorment='\\url',prefer_doi=True)
    s += "}\n"
    #+"}{"+"}"
    return s


def default_entry_filter(entry):
    """
    returns True
    :param entry:
    :return:
    """
    return True


def entry_filter_type(entry, type=''):
    """

    :param entry:
    :param type:
    :return:
    """
    if entry.entry_type.lower() == type:
        return True
    return False


def write_file_default(file, entries, entry_filter=default_entry_filter,
                       prefix='', suffix='', written=set()):
    """

    :param filename: name of a file
    :param entries: collection of bibentries
    :return: returns set of written items
    """
    file.write(prefix)
    #write entries
    for entry in entries:
        if entry_filter(entry) and (not entry in written):
            file.write(entry_to_tex(entry))
            written.add(entry)
    #write suffix
    file.write(suffix)

    return written





if __name__ == '__main__':
    from sys import argv

    my_args = getopts(argv)
    if '-f' in my_args:  # Example usage.
        filename = my_args['-f']
        print("Processing file: ", filename)
        print(my_args)
    else:
        print("Usage ... -f filename -p author_family_name")
        exit()

    person_name = None
    if '-p' in my_args:
        person_name = my_args['-p']
        print("Filtering person: ", person_name)

    entries = parse_bib_file(filename, person_name)
    sorted_entries = sorted(entries, key=get_sorting, reverse=True)
    #sorted_entries contain all the input
    for entry in sorted_entries:
        print(entry)

    file = open('publications.tex', 'w')
    #write prefix

    file.write(file_prefix)
    #writting out articles
    def my_filter(entry):
        return entry_filter_type(entry, type='article')
    written = write_file_default(file, sorted_entries,
                                 entry_filter=my_filter,
                                 prefix='\\ecvitem{\\highlight{Publications}}{Journal Articles}\n')
    write_file_default(file, sorted_entries,
                       prefix='\\ecvitem{\\highlight{Other publications}}{}\n',
                       written=written)

    file.write(file_suffix)
    file.close()



