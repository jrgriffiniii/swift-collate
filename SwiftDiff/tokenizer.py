# -*- coding: utf-8 -*-

from nltk.tokenize.punkt import PunktWordTokenizer
# from nltk.tokenize import TreebankWordTokenizer
import networkx as nx
import re
import nltk
import string
from copy import deepcopy
from lxml import etree

from difflib import ndiff

class TextToken:

    def __init__(self, ngram):

        self.value = ngram

    def __str__(self):

        return self.value

    @staticmethod
    def classes(ngram):

        output = ngram
        classes = []

        for element_name, element_classes in { 'indent': ['indent'],
                                               'display-initial': [ 'display-initial' ],
                                               'black-letter': [ 'black-letter' ],
                                               }.iteritems():

            if re.match(element_name.upper() + '_ELEMENT', output) or re.match(element_name.upper() + '_CLASS_OPEN', output):

                classes.extend(element_classes)
        return classes

    # This provides the HTML markup for the intermediary strings used for tokenization
    #
    @staticmethod
    def escape(ngram):

        output = ngram

        for class_name, markup in { 'italic': [ '<i>', '</i>' ],
                                    'display-initial': [ '<span>', '</span>' ],
                                    'underline': [ '<u>', '</u>' ],
                                    'small-caps': [ '<small>', '</small>' ],
                                    'black-letter': [ '<span>', '</span>' ],
                                    }.iteritems():

            class_closed_delim = class_name.upper() + '_CLASS_CLOSED'
            class_opened_delim = class_name.upper() + '_CLASS_OPEN'

            # Anomalous handling for cases in which the display initials are capitalized unnecessarily
            #
            if class_name == 'display-initial':

                #output = re.sub(class_name.upper() + '_CLASS_CLOSED', markup[-1], output)
                #output = re.sub(class_name.upper() + '_CLASS_OPEN', markup[0], output)

                # output = output.lower().capitalize()

                markup_match = re.match( re.compile(class_opened_delim + '(.+?)' + class_closed_delim + '(.+?)\s?'), output )

                if markup_match:

                    markup_content = markup_match.group(1) + markup_match.group(2)

                    output = re.sub( re.compile(class_opened_delim + '(.+?)' + class_closed_delim + '(.+?)\s?'), markup[0] + markup_content.lower().capitalize() + markup[1], output )
            else:

                #output = re.sub(class_name.upper() + '_CLASS_CLOSED', markup[-1], output)
                #output = re.sub(class_name.upper() + '_CLASS_OPEN', markup[0], output)
                output = re.sub( re.compile(class_opened_delim + '(.+?)' + class_closed_delim), markup[0] + '\\1' + markup[1], output )

        for element_name, markup in { 'gap': '<br />',
                                      'indent': '<span class="indent">&#x00009;</span>',
                                      }.iteritems():

            output = re.sub(element_name.upper() + '_ELEMENT', markup, output)

        return output

class Line:

    # @todo Refactor with TextToken.classes
    #
    @staticmethod
    def classes(line):

        output = line
        classes = []

        for element_name, element_classes in { 'indent': ['indent'],
                                               # 'display-initial': [ 'display-initial' ]
                                               'black-letter': [ 'black-letter' ]
                                               }.iteritems():

            if re.match(element_name.upper() + '_ELEMENT', output) or re.match(element_name.upper() + '_CLASS_OPEN', output):

                classes.extend(element_classes)
        return classes

    # @todo Refactor with TextToken.escape
    #
    @staticmethod
    def escape(line):

        output = line

        for class_name, markup in { 'italic': [ '<i>', '</i>' ],

                                    'display-initial': [ '<span class="display-initial">', '</span>' ],
                                    'underline': [ '<u>', '</u>' ],

                                    'small-caps': [ '<small>', '</small>' ],
                                    'black-letter': [ '<span>', '</span>' ],
                                    }.iteritems():

            class_closed_delim = class_name.upper() + '_CLASS_CLOSED'
            class_opened_delim = class_name.upper() + '_CLASS_OPEN'

            if class_name == 'display-initial':

                # markup_match = re.match( re.compile(class_opened_delim + '(.+?)' + class_closed_delim), output )
                markup_match = re.match( re.compile(class_opened_delim + '(.+?)' + class_closed_delim + '(.+?\s+?)'), output )

                if markup_match:

                    # output = re.sub( re.compile(class_opened_delim + '(.+?)' + class_closed_delim), markup[0] + markup_match.group(1).lower().capitalize() + markup[1], output )
                    markup_content = markup_match.group(1) + markup_match.group(2)

                    output = re.sub( re.compile(class_opened_delim + '(.+?)' + class_closed_delim + '(.+?\s+?)'), markup[0] + markup_content.lower().capitalize() + markup[1], output )
            else:

                output = re.sub( re.compile(class_opened_delim + '(.+?)' + class_closed_delim), markup[0] + '\\1' + markup[1], output )

        for element_name, markup in { 'gap': '<br />',
                                      'indent': '<span class="indent">&#x00009;</span>'
                                      }.iteritems():

            output = re.sub(element_name.upper() + '_ELEMENT', markup, output)

        return output

class ElementToken:  

    def __init__(self, name=None, attrib=None, children=None, text=None, doc=None, **kwargs):

        if doc is not None:

            name = doc.xpath('local-name()')
            attrib = doc.attrib
            children = list(doc)
            text = string.join(list(doc.itertext())) if doc.text is not None else ''

            # Work-around
            parents = doc.xpath('..')
            parent = parents.pop()

            # parent_name = parent.xpath('local-name()')
            parent_name = parent.xpath('local-name()') + ' n="' + parent.get('n') + '"' if name == 'l' else parent.xpath('local-name()')

            # print etree.tostring(doc)

        self.name = name
        self.attrib = attrib

        # Generate a string consisting of the element name and concatenated attributes (for comparison using the edit distance)
        # Note: the attributes *must* be order by some arbitrary feature

        # Work-around for the generation of normalized keys (used during the collation process)
        # @todo Refactor
        if self.name == 'lg':

            self.value = '<' + parent_name + '/' + self.name
            attribs = [(k,v) for (k,v) in attrib.iteritems() if k == 'n']

            pass
        elif self.name == 'l':

            self.value = '<' + parent_name + '/' + self.name
            # self.value = '<' + self.name
            attribs = [(k,v) for (k,v) in attrib.iteritems() if k == 'n']

        else:

            self.value = '<' + self.name
            attribs = self.attrib.iteritems()

        # Generate the key for the TEI element
        for attrib_name, attrib_value in attribs:

            self.value += ' ' + attrib_name + '="' + attrib_value + '"'
        self.value += ' />'

        self.children = children

        # Parsing for markup should occur here
        if name == 'l' or name == 'p':

            doc_markup = etree.tostring(doc)
            for feature in [{'xml': '<hi rend="italic">', 'text_token': 'italic'},
                            {'xml': '<hi rend="display-initial">', 'text_token': 'display-initial'},
                            {'xml': '<hi rend="underline">', 'text_token': 'underline'},
                            {'xml': '<gap>', 'text_token': 'gap'}]:

                feature_xml = feature['xml']

                doc_markup = re.sub(feature_xml , string.upper(feature['text_token']) + u"_CLASS_OPEN", doc_markup)
            doc_markup = re.sub('</hi>', u"_CLASS_CLOSED", doc_markup)

            new_doc = etree.fromstring(doc_markup)
            text = string.join(list(new_doc.itertext())) if new_doc.text is not None else ''

        # Insert the identation values for the rendering
        if 'rend' in attrib:

            rend = attrib['rend']
            indent_match = re.match(r'indent\((\d)\)', rend)
            if indent_match:

                indent_value = int(indent_match.group(1))
                # indent_tokens = [u"«indent»"] * indent_value
                indent_tokens = [u"INDENT_ELEMENT"] * indent_value
                indent = ''.join(indent_tokens)

                text = indent + text

        self.text = text

class DiffFragmentParser:

    @staticmethod
    def parse(tree):

        pass

# The "Diff Fragment" Entity passed to the Juxta visualization interface

# The following JSON is retrieved from the server
# [{
#     "range": {
#         "start": 19,
#         "end": 29
#     },
#     "witnessName": "welcome2",
#     "typeSymbol": "&#9650;&nbsp;",
#     "fragment": " to Juxta! / <span class='change'>In getting</span> started, you should..."
# }]

class DiffFragment:

    @staticmethod
    def format_fragment(srcFrag, origRange = [], contextRange = [], maxLen=None):

        pass

    def __init__(self, start, end, witness_name, edit_dist, fragment):

        self.range = [start, end]
        self.witness_name = witness_name

        if edit_dist > -1:

            self.type_symbol = "&#9650;&nbsp;"
        elif edit_dist == 0:

            self.type_symbol = "&#10006;&nbsp;";
        else:

            self.type_symbol = "&#10010;&nbsp;"
        
        self.fragment = fragment

class ComparisonSetTei:
    """
    Class for TEI Parallel Segmentation Documents serializing Juxta WS Comparison Sets
    """

    tei_doc = """
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title>set_a</title>
                <respStmt>
                    <resp>Conversion from Juxta comparison set to TEI-conformant markup</resp>
                    <name>Generated by the Swift Diff Service for Juxta Commons</name>
                </respStmt>
            </titleStmt>
            <publicationStmt><p/></publicationStmt>
            <sourceDesc><p/></sourceDesc>
        </fileDesc>
        <encodingDesc>
            <variantEncoding location="internal" method="parallel-segmentation"/>
        </encodingDesc>
    </teiHeader>
    
    <text>
        <front>
            <div>
                <listWit>
                    <witness xml:id="wit-1136">source_b</witness>
                    <witness xml:id="wit-1135">source_a</witness>
                </listWit>
            </div>
        </front>
        <body>
            <p>     Songs of Innocence<lb/> # <head>Songs of Innocence</head>
 <lb/>
  Introduction<lb/>
  Piping down the valleys wild, <lb/>
 Piping songs of pleasant glee, <lb/>
 On a cloud I saw a child, <lb/>
 And he laughing said to me: <lb/>
 <lb/>
 <lb/>
 <lb/>
 <lb/>
 <lb/>
 </p>
        </body>
    </text>
</TEI>
"""

    def __init__(self, witnesses):

        self.witnesses = witnesses

        self.doc = etree.parse(self.tei_doc)

        list_wit_elems = self.doc.xpath('tei:text/tei:front/tei:div/tei:listWit')
        self.list_wit = list_wit_elems.pop()

        body_elems = self.doc.xpath('tei:text/tei:body')
        self.body = body_elems.pop()

    def parse(self):

        for witness in self.witnesses:

            self.append_witness(witness)

    def append_witness(self, witness):

        # The ID's are arbitrary, but they must be unique
        # The Witnesses are created anew if they do not exist within the system, and assigned new ID's
        witness_elem = Element('tei:witness', 'xml:id="wit-' + witness.id + '"')
        self.list_wit.append(witness_elem)

        # Update the raw XML for the witness using SQL
        

        # Append elements from the diff tree
        self.body.append()

class Alignment:

    # Generate the path using the optimal alignment

    # Andrew McCallum's (UMass Amherst) implementation seems to a popular implementation referenced frequently:
    # http://people.cs.umass.edu/~mccallum/courses/cl2006/lect4−stredit.pdf
    def stredit(self, u, v):
        "Calculate Levenstein edit distance for strings s1 and s2."

        len1 = len(u) # vertically
        len2 = len(v) # horizontally

        # Allocate the table
        self.table = [None]*(len2+1)
        for i in range(len2+1): table[i] = [0]*(len1+1)

        # Initialize the table
        for i in range(1, len2+1): table[i][0] = i # Populate the first row with values
        for i in range(1, len1+1): table[0][i] = i # Populate the first column with values

        # Do dynamic programming
        for i in range(1,len2+1):

            for j in range(1,len1+1):

                if u[j-1] == v[i-1]:

                    d = 0
                else:

                    d = 1
                    table[i][j] = min(table[i-1][j-1] + d, # Substitution
                                      table[i-1][j]+1, # Insertion
                                      table[i][j-1]+1) # Deletion

    # Needleman-Wunsch
    def nwunsch(self):

        pass

    # Smith-Waterman
    def swaterman(self):

        pass

    # Retrieve the optimal alignment path
    # Adapted from https://github.com/alevchuk/pairwise-alignment-in-python/blob/master/alignment.py
    def _alignment_path(self):

        # table = [ [1,2,3,4,5],
        #           [1,2,3,4,5],
        #           [2,3,3,4,5] ]

        # i = max(self.table[j])
        # j = max(self.table[i])
        i = len(v) + 1
        j = len(u) + 1

        path = []

        while i > 0 and j > 0:

            score_current = score[i][j]

            score_sub = score[i-1][j-1]
            score_delete = score[i][j-1]
            score_insert = score[i-1][j]

            if score_sub < score_current:

                path.append( SUB )

                i -= 1
                j -= 1
            elif score_insert < score_current:

                path.append( INS )

                j -= 1
            elif score_delete < score_current:

                path.append( DEL )

                i -= 1
            else:

                raise Exception('No possible alignment found')

        return path.reverse()

    def alignment_path(self):

        diff = ndiff('one\ntwo\nthree\n'.splitlines(1), 'ore\ntree\nemu\n'.splitlines(1))
        diff = list(diff)
        print ''.join(restore(diff, 1))

        pass

class Tokenizer:

    def __init__(self):

        pass

    # Construct a Document sub-tree consisting solely of stanzas or paragraphs from any given TEI-encoded text
    @staticmethod
    def parse_stanza(resource):

        with open(resource) as f:

            data = f.read()
            doc = etree.fromstring(data)
            elems = doc.xpath('//tei:lg', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
            elem = elems.pop()

        return elem

    @staticmethod
    def parse_text(resource):

        with open(resource) as f:

            data = f.read()
            doc = etree.fromstring(data)
            elems = doc.xpath('//tei:text', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
            elem = elems.pop()

        return elem

    # Construct the Document tree for tei:text elements
    # The output is passed to either Tokenizer.diff() or Tokenizer.stemma()
    # This deprecates Tokenizer.parse()
    # The root node should have one or many <lg> child nodes
    @staticmethod
    def text_tree(text_node, name=''):

        lg_nodes = text_node.xpath('//tei:lg', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})

        if not lg_nodes:

            raise Exception("Could not retrieve any <lg> nodes for the following TEI <text> element: " + etree.tostring(text_node))

        token_tree = nx.Graph()
        token_tree.name = name

        for lg_node in lg_nodes:

            lg_tree = Tokenizer.parse(lg_node, name)
            token_tree = nx.compose(token_tree, lg_tree)

        return token_tree

    @staticmethod
    def parse_child(child):
        
        child_text = child.text if child.text is not None else ''
        child_tail = child.tail if child.tail is not None else ''

        output = child_text + child_tail

        if child.xpath('local-name()') == 'gap':

            output = child.xpath('local-name()').upper() + u"_ELEMENT" + child_tail

        elif child.get('rend'):

            output = child.get('rend').upper() + u"_CLASS_OPEN" + child_text + child.get('rend').upper() + u"_CLASS_CLOSED" + child_tail

        return output

    # Construct the Document tree
    # The root node should be a <lg> node
    @staticmethod
    def parse(node, name=''):

        # Initialize an undirected graph for the tree, setting the root node to the lxml node
        token_tree = nx.Graph()

        token_tree.name = name

        # Parsing must be restricted to the '<l>' and '<p>' depth
        # @todo Refactor
        if node.xpath('local-name()') not in ['l', 'p']:

            children = list(node)
        
            # If the lxml has no more nodes, return the tree
            if len(children) == 0:

                return token_tree

            sub_trees = map(Tokenizer.parse, children)

            for sub_tree in map(Tokenizer.parse, children):

                token_tree = nx.compose(token_tree, sub_tree)

            return token_tree

        # Parsing node content
        #
        node_tail = '' if node.tail is None else node.tail
        node_text_head = unicode(node.text) if node.text is not None else ''
        node_text = node_text_head + string.join(map( Tokenizer.parse_child, list(node.iterchildren())), '') + node_tail
        node.text = node_text

#        node_markup = etree.tostring(node)
#        for feature in [{'xml': '<hi rend="italic">', 'text_token': 'italic'},
#                        {'xml': '<hi rend="display-initial">', 'text_token': 'display-initial'},
#                        {'xml': '<hi rend="underline">', 'text_token': 'underline'},
#                        {'xml': '<gap>', 'text_token': 'gap'}]:

#            feature_xml = feature['xml']

#            node_markup = re.sub(feature_xml + '(.+?)' + '</hi>', u"_CLASS_OPEN\\1_CLASS_CLOSED", node_markup)

#            new_node = etree.fromstring(node_markup)
            # text = string.join(list(new_node.itertext())) if new_node.text is not None else ''
#            node.text = string.join(list(new_node.itertext())) if new_node.text is not None else ''

        # Footnotes are not to be removed, but instead, are to be appended following each line

        # Store the footnotes within a separate tree for comparison
        footnote_tree = etree.fromstring('''
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div1 type="book">
	<div2 type="poem">
	  <lg n="1">
	    <l n="1" />
	  </lg>
	</div2>
      </div1>
    </body>
  </text>
</TEI>''')

        footnotes = footnote_tree.xpath('//tei:l[@n="1"]', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}).pop()

        for footnote in node.xpath("//tei:note[@place='foot']", namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            
            # Append the footnote to the tree
            # footnotes.append(deepcopy(footnote))

            # Ensure that all text trailing the footnote element is preserved
            parent = footnote.getparent()

            parent_text = '' if parent.text is None else parent.text
            footnote_tail = '' if footnote.tail is None else footnote.tail
            parent.text = parent_text + footnote_tail

            # Footnotes are not to be removed, but instead, are to be appended following each line
            # node.append( deepcopy(footnote) )

            # Remove the footnote itself
            footnote.getparent().remove(footnote)

        # Handling for typographic feature (e. g. <hi />) and editorial elements (e. g. <gap />)
        # Leave intact; Prefer transformation into HTML5 using XSL Stylesheets

# before
# <hi xmlns="http://www.tei-c.org/ns/1.0" rend="SMALL-CAPS">NCE</hi> on a Time, near 
# <l xmlns="http://www.tei-c.org/ns/1.0" rend="indent(1)" n="3">UNDERLINE_CLASS_OPENChannel-Row_CLASS_CLOSED,<hi rend="SMALL-CAPS">NCE</hi> on a Time, near </l>
# after
# <l xmlns="http://www.tei-c.org/ns/1.0" rend="indent(1)" n="3">SMALL-CAPS_CLASS_OPENNCE_CLASS_CLOSED on a Time, near <hi rend="SMALL-CAPS">NCE</hi> on a Time, near </l>

#                    parent_markup = re.sub('<hi xmlns="http://www.tei-c.org/ns/1.0" rend="' + feature_token + '">', feature_token.upper() + u"_CLASS_OPEN", parent_markup)
#                    parent_markup = re.sub('<hi rend="' + feature_token + '">', feature_token.upper() + u"_CLASS_OPEN", parent_markup)
#                    parent_markup = re.sub('</hi>', u"_CLASS_CLOSED", parent_markup)


        for feature in [{'xpath': 'tei:hi[@rend="italic"]', 'text_token': 'italic', 'tag': 'hiitalic'},
                        {'xpath': 'tei:hi[@rend="display-initial"]', 'text_token': 'display-initial', 'tag': 'hidisplay-italic'},
                        {'xpath': 'tei:hi[@rend="underline"]', 'text_token': 'underline', 'tag': 'hiunderline'},

                        # {'xpath': 'tei:hi[@rend="SMALL-CAPS"]', 'text_token': 'small-caps', 'tag': 'hismall-caps'},
                        {'xpath': 'tei:hi[@rend="SMALL-CAPS"]', 'text_token': 'SMALL-CAPS', 'tag': 'hismall-caps'},

                        {'xpath': 'tei:hi[@rend="sup"]', 'text_token': 'superscript', 'tag': 'hisuperscript'},
                        {'xpath': 'tei:hi[@rend="black-letter"]', 'text_token': 'black-letter', 'tag': 'hiblack-letter'},
                        {'xpath': 'tei:gap', 'text_token': 'gap', 'tag': 'gap'}]:

            feature_xpath = feature['xpath']
            feature_token = feature['text_token']
            feature_tag = feature['tag']

            feature_elements = node.xpath(feature_xpath, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
            # feature_elements = [ feature_elements[0] ] if len(feature_elements) > 0 else []

            for feature_element in feature_elements:

                # Resolving SPP-178
                # Ensure that the children are parsed only once
                # However, all feature elements must still be removed

                # Ensure that all text trailing the feature_element element is preserved
                parent = feature_element.getparent()

                parent_tail = parent.tail if parent.tail is not None else ''

                # Currently leads to issues relating to the parsing of redundant, trailing tokens
                # @todo Resolve SPP-178

#                parent_text_head = unicode(parent.text) if parent.text is not None else ''
#                parent_text = parent_text_head + string.join(map( Tokenizer.parse_child, list(parent.iterchildren())), '') + parent_tail
#                parent.text = parent_text

                feature_element.getparent().remove(feature_element)


        token_tree_root = ElementToken(doc=node)

        # For the text of the node, use the PunktWordTokenizer to tokenize the text
        # Ensure that each tokenized n-gram is linked to the lxml token for the tree:
        #    o
        # /     \
        # n-gram n-gram

        # text_tokens = tokenizer.tokenize( token_tree_root.text )
        text_tokens = [ token_tree_root.text ]

        init_dist = 0

        # Introduce the penalty for stylistic or transcription elements
        # @todo This also requires some problematic restructuring of footnote and rendering elements (as these are *not* leaves)

        # text_token_edges = map(lambda token: (token_tree_root, TextToken(token)), text_tokens )
        text_token_edges = map(lambda token: (token_tree_root.value, token, { 'distance': init_dist }), text_tokens )
        # text_token_edges = map(lambda token: (token_tree_root, token), text_tokens )

        token_tree.add_edges_from(text_token_edges)

        children = list(node)
        
        # If the lxml has no more nodes, return the tree
        if len(children) == 0:

            return token_tree

        # ...otherwise, merge the existing tree with the sub-trees generated by recursion
        sub_trees = map(Tokenizer.parse, children)

        for sub_tree in map(Tokenizer.parse, children):

            token_tree = nx.compose(token_tree, sub_tree)

        return token_tree

    # Generates a stemmatic tree consisting of many witness TEI Documents in relation to a single base Document    
    @staticmethod
    def stemma(root_witness, witnesses): # Root text of the stemma

        diff_tree = nx.Graph()

        roots = [ root_witness ] * len(witnesses)
        for text_u, text_v in zip(roots, witnesses):

            node_u = text_u['node']
            text_u_id = text_u['id']
            node_v = text_v['node']
            text_v_id = text_v['id']

            diff_u_v_tree = Tokenizer.diff(node_u, text_u_id, node_v, text_v_id)

            diff_tree = nx.compose(diff_tree, diff_u_v_tree)

        # Merging the bases manually is necessary (given that each TextToken Object is a unique key for the graph structure
        # @todo Investigate cases in which TextToken Objects can be reduced simply to string Objects
        # (Unfortunately, the problem still exists in which identical string content between lines can lead to collisions within the graph structure)
        edges = diff_tree.edges()
        filtered_edges = []
        filtered_diff_tree = nx.Graph()

        base_line_edges = []

        for edge in edges:

            u = edge[0]

            filtered_edge = []

            for edge_item in diff_tree[u].items(): # For each edge between the line expression u and the related TextNodes...

                line_text = edge_item[0]
                line_attributes = edge_item[-1]
                if(line_attributes['feature'] == 'line' and line_attributes['witness'] == 'base'): # Ensure that lines are index uniquely

                    if not unicode(u) in base_line_edges:

                        base_line_edges.append(unicode(u))
                        filtered_diff_tree.add_edge(u, line_text, line_attributes)

                else:

                    # filtered_edge.append(edge_item)
                    filtered_diff_tree.add_edge(u, line_text, line_attributes)

        # return diff_tree
        # filtered_diff_tree.add_edges_from(tuple(filtered_edges))
        
        return filtered_diff_tree

    @staticmethod
    def clean_tokens(tokens):

        output = []
        
        i=0
        j=0
        while i < len(tokens) - 1:

            u = tokens[i]
            v = tokens[i+1]

            # Ensure that initial quotation marks are joined with proceeding tokens
            if u in string.punctuation or u[0] in string.punctuation:

                if len(output) == 0:

                    output.append(u + v)
                else:

                    output = output + [ u + v ]
                i+=1
            else:

                output.append(u)

            if v in string.punctuation or v[0] in string.punctuation:

                output = output + [ u + v ]
                i+=1

            i+=1

        return output

    # Generates a tree structuring the differences identified within two given TEI Documents
    @staticmethod
    def diff(node_u, text_u_id, node_v, text_v_id):

#        print 'trace3'
#        print node_u
        
        # Each node serves as a <tei:text> element for the text being compared
        tree_u = Tokenizer.text_tree(node_u, text_u_id)
        text_u_id = tree_u.name if text_u_id is None else text_u_id

        tree_v = Tokenizer.text_tree(node_v, text_v_id)
        text_v_id = tree_v.name if text_v_id is None else text_v_id

        diff_tree = nx.Graph()

        # Assess the difference in tree structure
        # diff_tree = nx.difference(tree_u, tree_v)

        # Calculate the edit distance for each identical node between the trees

        # Retrieve the common edges
        # intersect_tree = nx.intersection(tree_u, tree_v)

        # Iterate through each edge
        # for edge in intersect_tree.edges(data=True):
        for u, v, data in tree_u.edges(data=True):

            # Only perform the edit distance for text nodes
            # edit_dist = nltk.metrics.distance(tree_u[u], tree_v[u])
            # (u, u, edit_dist)

            # text_nodes = filter( lambda e: e.__class__.__name__ != 'ElementToken', [u,v] )
            text_nodes = filter( lambda e: not re.match(r'^<', e), [u,v] )

            if len(text_nodes) > 1:

                raise Exception("Text nodes can not be linked to text nodes", text_nodes)
            elif len(text_nodes) == 0:

                # Comparing elements
                raise Exception("Structural comparison is not yet supported")
            else:
                
                text_node_u = string.join(text_nodes)
                elem_node_u = v if u == text_node_u else u
                nodes_u_dist = data['distance']

                # If there is no matching line within the stanza being compared, simply avoid the comparison altogether
                # @todo Implement handling for addressing structural realignment between stanzas (this would likely lie within Tokenizer.parse_text)
                if not elem_node_u in tree_v:

                    # Try to structurally align the lines by one stanza
                    stanza_node_u_m = re.search('<lg n="(\d+)"/l n="(\d+)"', elem_node_u)
                    if stanza_node_u_m:

                        stanza_index = int(stanza_node_u_m.group(1))

                        line_index = int(stanza_node_u_m.group(2))

                        elem_node_u_incr = re.sub('lg n="(\d+)"', 'lg n="' + str(stanza_index + 1) + '"', elem_node_u)
                        elem_node_u_decr = re.sub('lg n="(\d+)"', 'lg n="' + str(stanza_index - 1) + '"', elem_node_u)

                        if elem_node_u_incr in tree_v:

                            elem_node_v = tree_v[elem_node_u_incr]

                        elif stanza_index > 0 and elem_node_u_decr in tree_v:

                            elem_node_v = tree_v[elem_node_u_decr]
                        else:

                            continue

                    else:
                        
                        # raise Exception("Failed to parse the XML for the following: " + elem_node_u)
                        continue

                else:

                    elem_node_v = tree_v[elem_node_u]
                    
                text_nodes_v = elem_node_v.keys()
                
                text_node_v = string.join(text_nodes_v)

                # If the text node has not been linked to the <l> node, attempt to match using normalization

#                nodes_v_dist = 0
#                if not text_node_v in elem_node_v:

#                    text_node_v = text_node_v.strip()
#                    text_node_v_norm = re.sub(r'\s+', '', text_node_v)

#                    for text_node_u in elem_node_v.keys():

#                        text_node_u_norm = re.sub(r'\s+', '', text_node_u)
#                        if text_node_v_norm == text_node_u_norm:

#                            nodes_v_dist = elem_node_v[text_node_u]['distance']

#                    if not text_node_v in elem_node_v:

#                        nodes_v_dist = 0
#                    if nodes_v_dist is None:

#                        raise Exception('Could not match the variant text string :"' + text_node_v + '" to those in the base: ' + string.join(elem_node_v.keys()) )
#                else:

                if not text_node_v in elem_node_v:

                    nodes_v_dist = 0
                else:

                    nodes_v_dist = elem_node_v[text_node_v]['distance']

                # Just add the edit distance
                edit_dist = nodes_u_dist + nodes_v_dist + nltk.metrics.distance.edit_distance(text_node_u, text_node_v)

                # Debugging
                # if re.match(r"n=\"10\"", elem_node_u):
                # if elem_node_u == '<lg n="1"/l n="3" />':
#                print 'adding the edges'
#                print elem_node_u
#                print text_node_u
                
                # Note: This superimposes the TEI structure of the base text upon all witnesses classified as variants
                # Add an edge between the base element and the base text
                diff_tree.add_edge(elem_node_u, TextToken(text_node_u), distance=0, witness=text_u_id, feature='line')

                # Add an additional edge between the base element and the base text
                diff_tree.add_edge(elem_node_u, TextToken(text_node_v), distance=edit_dist, witness=text_v_id, feature='line')

                # Now, add the tokenized texts
                # Default to the Treebank tokenizer
                # text_tokenizer = TreebankWordTokenizer()
                text_tokenizer = PunktWordTokenizer()

#                text_tokens_u = text_tokenizer.tokenize(text_node_u)
#                text_tokens_u = Tokenizer.clean_tokens(text_tokens_u)

#                text_tokens_v = text_tokenizer.tokenize(text_node_v)
#                text_tokens_v = Tokenizer.clean_tokens(text_tokens_v)
                text_tokens_u = text_node_u.split()
                text_tokens_v = text_node_v.split()

                # Debugging

                # Attempt to align the sequences (by adding gaps where necessary)
                # THIS HAS BEEN TEMPORARILY DISABLED
                # Strip all tags and transform into the lower case
                # Here is where the edit distance is to be inserted
                text_tokens_u_len = len(text_tokens_u)
                text_tokens_v_len = len(text_tokens_v)

                # if text_tokens_u_len != text_tokens_v_len and min(text_tokens_u_len, text_tokens_v_len) > 0:
                if False:

                    for i, diff in enumerate(ndiff(text_tokens_u, text_tokens_v)):

                        opcode = diff[0:1]
                        if opcode == '+':

                            text_tokens_u = text_tokens_u[0:i] + [''] + text_tokens_u[i:]
                            # pass

                        elif opcode == '-':

                            text_tokens_v = text_tokens_v[0:i] + [''] + text_tokens_v[i:]
                            # pass

                # Deprecated

#                print "after"
#                print "\n"
#                print [ (i,e) for (i,e) in enumerate(text_tokens_u) ]
#                print "\n"
#                print [ (i,e) for (i,e) in enumerate(text_tokens_v) ]
                # print enumerate(text_tokens_v)
                                    
                # text_tokens_intersect = filter(lambda t: t in text_tokens_v, text_tokens_u)
                text_tokens_intersect = [ (i,e) for (i,e) in enumerate(text_tokens_u) if i < len(text_tokens_v) and text_tokens_v[i] == e ]

                # max_text_tokens = max(len(text_tokens_u), len(text_tokens_v))
                # text_tokens_intersect = [''] * max_text_tokens
                # text_tokens_diff_u = [''] * max_text_tokens

                # text_tokens_diff_u = filter(lambda t: not t in text_tokens_v, text_tokens_u)
                # text_tokens_diff_u = [ (i,e) for (i,e) in enumerate(text_tokens_u) if i < len(text_tokens_v) and text_tokens_v[i] != e ]
                text_tokens_diff_u = [ (i,e) for (i,e) in enumerate(text_tokens_u) if i < len(text_tokens_v) ]
                
#                print 'tokens in u'
#                print text_tokens_u
#                print 'tokens in v'
#                print text_tokens_v

#                print elem_node_u
#                print 'tokens in u and v'
#                print text_tokens_intersect
#                print 'tokens in just u'
#                print text_tokens_diff_u

                # text_tokens_diff_v = [t for t in text_tokens_v if not t in text_tokens_u]
                # text_tokens_diff_v = [ (i,e) for (i,e) in enumerate(text_tokens_v) if i < len(text_tokens_u) and text_tokens_u[i] != e ]
                text_tokens_diff_v = [ (i,e) for (i,e) in enumerate(text_tokens_v) if i < len(text_tokens_u) ]

#                print 'tokens in just v'
#                print text_tokens_diff_v

                # Edges override the different tokens
                # "line of tokens"
                # |    \  \
                # line of tokens

#                print 'trace5: tokens for ' + elem_node_u
#                print diff_tree[elem_node_u]

                # For tokens in both sets
                for pos,text_token in text_tokens_intersect:

                    # pos = text_tokens_u.index(text_token)
                    # diff_tree.add_edge(elem_node_u, text_token, distance=0, witness='base', feature='ngram', position=pos)

#                    print 'Adding the token "' + text_token + '" for the line ' + elem_node_u + 'at the position ' + str(pos) + ' for the witness common'

                    token = TextToken(text_token)
                    # diff_tree.add_edge(elem_node_u, token, distance=0, witness='common', feature='ngram', position=pos)

#                print 'trace4: tokens for ' + elem_node_u
#                print diff_tree[elem_node_u]

                # @todo Refactor
                for pos,text_token in text_tokens_diff_u:

                    # pos = text_tokens_u.index(text_token)
                    # diff_tree.add_edge(elem_node_u, '_' + text_token, distance=0, witness=text_u_id, feature='ngram', position=pos)

#                    print 'Adding the token "' + text_token + '" for the line ' + elem_node_u + 'at the position ' + str(pos) + ' for the witness ' + text_u_id

                    token = TextToken(text_token)
                    diff_tree.add_edge(elem_node_u, token, distance=0, witness=text_u_id, feature='ngram', position=pos)

                # @todo Refactor
                for pos,text_token in text_tokens_diff_v:

                    # Disjoint
                    # pos = text_tokens_v.index(text_token)
                    # diff_tree.add_edge(elem_node_u, '__' + text_token, distance=None, witness=text_v_id, feature='ngram', position=pos)

#                    print 'Adding the token "' + text_token + '" for the line ' + elem_node_u + 'at the position ' + str(pos) + ' for the witness ' + text_v_id

                    token = TextToken(text_token)
#                    diff_tree.add_edge(elem_node_u, token, distance=None, witness=text_v_id, feature='ngram', position=pos)
                    diff_tree.add_edge(elem_node_u, token, distance=nltk.metrics.distance.edit_distance(text_tokens_u[pos], token.value), witness=text_v_id, feature='ngram', position=pos)
                    
            pass

        return diff_tree
