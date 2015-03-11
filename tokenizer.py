# -*- coding: utf-8 -*-

from nltk.tokenize.punkt import PunktWordTokenizer
# from nltk.tokenize import TreebankWordTokenizer
import networkx as nx
import re
import nltk
import string
from copy import deepcopy
from lxml import etree

class TextToken:

    def __init__(self, ngram):

        self.value = ngram

class ElementToken:  

    def __init__(self, name=None, attrib=None, children=None, text=None, doc=None, **kwargs):

        if doc is not None:

            name = doc.xpath('local-name()')
            attrib = doc.attrib
            children = list(doc)
            text = string.join(list(doc.itertext())) if doc.text is not None else ''

            # print etree.tostring(doc)

        self.name = name
        self.attrib = attrib

        # Generate a string consisting of the element name and concatenated attributes (for comparison using the edit distance)
        # Note: the attributes *must* be order by some arbitrary feature

        self.value = '<' + self.name
        for attrib_name, attrib_value in self.attrib.iteritems():
            
            self.value += ' ' + attrib_name + '="' + attrib_value + '"'
        self.value += ' />'

        self.children = children

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


class Tokenizer:

    def __init__(self):

        pass

    @staticmethod
    def parse_stanza(resource):

        with open(resource) as f:

            data = f.read()
            doc = etree.fromstring(data)
            elems = doc.xpath('//tei:lg', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
            elem = elems.pop()

        return elem

    # Construct the parse tree
    # Each element is a node distinct from the 
    @staticmethod
    def parse(node, name=''):

        # Initialize an undirected graph for the tree, setting the root node to the lxml node
        token_tree = nx.Graph()

        token_tree.name = name

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

        for feature in [{'xpath': '//tei:hi[@rend="italic"]', 'text_token': 'italic'},
                        {'xpath': '//tei:hi[@rend="display-initial"]', 'text_token': 'display-initial'},
                        {'xpath': '//tei:hi[@rend="underline"]', 'text_token': 'underline'},
                        {'xpath': '//tei:gap', 'text_token': 'gap'}]:

            feature_xpath = feature['xpath']
            feature_token = feature['text_token']

            for feature_element in node.xpath(feature_xpath, namespaces={'tei': 'http://www.tei-c.org/ns/1.0'}):
            
                # Ensure that all text trailing the feature_element element is preserved
                parent = feature_element.getparent()
                feature_element_text = '' if feature_element.text is None else feature_element.text

                # print etree.tostring(feature_element)
                # print parent.text
                # print feature_element_text

                # Work-around for lxml
                if parent.text is None: parent.text = ''

                if feature_element_text:

                    parent.text += u"«" + feature_token + u"»" + feature_element_text + u"«" + feature_token + u"»" + feature_element.tail
                else:

                    parent.text += u"«" + feature_token + u"»" + feature_element.tail

                # Remove the feature_element itself
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

    @staticmethod
    def diff(node_u, text_u_id, node_v, text_v_id):

        tree_u = Tokenizer.parse(node_u, text_u_id)
        # text_u_id = tree_u.name

        # @todo Refactor for a list of variants
        tree_v = Tokenizer.parse(node_v, text_v_id)
        # text_v_id = tree_v.name

#        print tree_u.edges()
#        print tree_v.edges()

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
                assert False
            else:
                
                text_node_u = string.join(text_nodes)
                elem_node_u = v if u == text_node_u else u
                nodes_u_dist = data['distance']

#                if elem_node_u not in tree_v:

#                    continue
                
                # Retrieve the same text node from the second tree

                # 
                if not elem_node_u in tree_v:

                    continue

                text_nodes_v = tree_v[elem_node_u].keys()
                
                text_node_v = string.join(text_nodes_v)
                nodes_v_dist = tree_v[elem_node_u][text_node_v]['distance']

#                print text_node_u
#                print text_node_v

                # Just add the edit distance
                edit_dist = nodes_u_dist + nodes_v_dist + nltk.metrics.distance.edit_distance(text_node_u, text_node_v)
                
                # Note: This superimposes the TEI structure of the base text upon all witnesses classified as variants
                # Add an edge between the base element and the base text
                diff_tree.add_edge(elem_node_u, TextToken(text_node_u), distance=0, witness=text_u_id, feature='line')

                # Add an additional edge between the base element and the base text
                diff_tree.add_edge(elem_node_u, TextToken(text_node_v), distance=edit_dist, witness=text_v_id, feature='line')

                # Now, add the tokenized texts
                # Default to the Treebank tokenizer
                # text_tokenizer = TreebankWordTokenizer()
                text_tokenizer = PunktWordTokenizer()
                text_tokens_u = text_tokenizer.tokenize(text_node_u)
                text_tokens_v = text_tokenizer.tokenize(text_node_v)

                # Attempt to align the sequences (by adding gaps where necessary)
                # Strip all tags and transform into the lower case
                # Here is where the edit distance is to be inserted

                # @todo Implement the sequence alignment
                # Retrieve the longest string
                text_align_base = max(text_tokens_u, text_tokens_v)
                text_align_witness = text_tokens_u if text_align_base is text_tokens_u else text_tokens_v

                # Look ahead by one (and only one) character
                # @todo Refactor for more complex matching schemes?
                for i, base_token in enumerate(text_align_base):

                    if i == 0: continue

                    witness_token = text_align_witness[i - 1]

                    # Strip all tags
                    base_token = re.sub(r'', '', base_token)

                    # Cast into the lower case
                    base_token = base_token.lower()

                    # Strip all leading and trailing whitespace
                    base_token = base_token.strip()

                    # Compare the actual text data itself
                    edit_dist = nltk.metrics.distance.edit_distance(base_token, witness_token)
                    if edit_dist == 0:

                        # 

                        pass
                    
                    
                    pass

                # text_tokens_intersect = filter(lambda t: t in text_tokens_v, text_tokens_u)
                text_tokens_intersect = [ (i,e) for (i,e) in enumerate(text_tokens_u) if i < len(text_tokens_v) and text_tokens_v[i] == e ]

                # max_text_tokens = max(len(text_tokens_u), len(text_tokens_v))
                # text_tokens_intersect = [''] * max_text_tokens
                # text_tokens_diff_u = [''] * max_text_tokens

                # text_tokens_diff_u = filter(lambda t: not t in text_tokens_v, text_tokens_u)
                text_tokens_diff_u = [ (i,e) for (i,e) in enumerate(text_tokens_u) if i < len(text_tokens_v) and text_tokens_v[i] != e ]
                
                print 'tokens in u'
                print text_tokens_u
                print 'tokens in v'
                print text_tokens_v

                print 'tokens in u and v'
                print text_tokens_intersect
                print 'tokens in just u'
                print text_tokens_diff_u

                # text_tokens_diff_v = [t for t in text_tokens_v if not t in text_tokens_u]
                text_tokens_diff_v = [ (i,e) for (i,e) in enumerate(text_tokens_v) if i < len(text_tokens_u) and text_tokens_u[i] != e ]

                print 'tokens in just v'
                print text_tokens_diff_v

                # Edges override the different tokens
                # "line of tokens"
                # |    \  \
                # line of tokens

                # For tokens in both sets
                for pos,text_token in text_tokens_intersect:

                    # print 'trace20'
                    # print text_token

                    # pos = text_tokens_u.index(text_token)
                    # diff_tree.add_edge(elem_node_u, text_token, distance=0, witness='base', feature='ngram', position=pos)

                    token = TextToken(text_token)
                    diff_tree.add_edge(elem_node_u, token, distance=0, witness='base', feature='ngram', position=pos)

                # @todo Refactor
                for pos,text_token in text_tokens_diff_u:

                    # pos = text_tokens_u.index(text_token)
                    # diff_tree.add_edge(elem_node_u, '_' + text_token, distance=0, witness=text_u_id, feature='ngram', position=pos)

                    token = TextToken(text_token)
                    diff_tree.add_edge(elem_node_u, token, distance=0, witness=text_u_id, feature='ngram', position=pos)

                # @todo Refactor
                for pos,text_token in text_tokens_diff_v:

                    # Disjoint
                    # pos = text_tokens_v.index(text_token)
                    # diff_tree.add_edge(elem_node_u, '__' + text_token, distance=None, witness=text_v_id, feature='ngram', position=pos)

                    token = TextToken(text_token)
                    diff_tree.add_edge(elem_node_u, token, distance=None, witness=text_v_id, feature='ngram', position=pos)
                pass

            pass

        # Generate the edit distance
        
        # Append the edge to the diff_tree, with the edit distance as the attribute

        return diff_tree
