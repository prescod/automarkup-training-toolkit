# Based on https://github.com/yetessam/convert-simple-html-messy/blob/main/htmltomarkdownconverter.py

# Run in python 3 or later
""" The following module is based upon the html2markdown David Lönnhager (dlon)
module"""
"""html2markdown converts an html string to markdown while preserving unsupported markup."""

import html2markdown
import re

from bs4 import BeautifulSoup, Doctype, element


from html2markdown import (_escapeCharacters, _supportedAttrs, _breakRemNewlines, _recursivelyValid, unicode)

class HTMLToMarkdownConverter:

	def __init__(self):

		self.supportedAttributes = (
				'a href',
				'a title',
				'audio src'
				'img alt',
				'img src',
				'img title',
				'video src'
			)


		self.inlineTags = {
			'a', 'abbr', 'acronym', 'audio', 'b', 'bdi', 'bdo', 'big', 'cite', 'code',
			'data', 'datalist', 'del', 'dfn', 'em', 'i', 'ins', 'kbd', 'label', 'map',
			'mark', 'meter', 'object', 'picture', 'q', 'ruby', 's', 'samp', 'select',
			'slot', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'svg', 'template',
			'textarea', 'time', 'u', 'tt', 'var', 'wbr'
		}

		
		# Dictionary mapping tag names to functions
		self.tag_processors = {
		
			'html': self._process_block, 
			'head': self._process_block, 
			'meta': self._process_block, 
			'title': self._process_block,
			'body': self._process_block, 
			'blockquote': self._process_blockquote,
			'a': self._process_a,
			'canvas': self._process_block, 
			'figure': self._process_block_keep_name,
			'figcaption': self._process_block,
			'footer': self._process_block,
			'h1': self._process_h,
			'h2': self._process_h,
			'h3': self._process_h,
			'h4': self._process_h,
			'h5': self._process_h,
			'h6': self._process_h,
			'hr': self._process_block,
			'ul': self._process_block,
			'ol': self._process_block,
			'p' : self._process_p, 
			'li': self._process_li,
			'img': self._process_img,
			'pre': self._process_pre,
			'code':	self._process_code,
			"title": self._process_ignorable,
		}


	# not used yet
	def get_conversion_mapping():

		conversion_mapping = {
				'p': {'before': '\n\n', 'after': '\n\n'},
				'br': {'before': '  \n', 'after': ''},
				'img': {'before': '![{alt}]({src}{title})', 'after': ''},
				'hr': {'before': '\n---\n', 'after': ''},
				'pre': {'before': '\n\n{code}', 'after': '\n\n'},
				'code': {'before': '`` {text} ``', 'after': ''},
				'blockquote': {'before': '<<<BLOCKQUOTE: {text}>>>', 'after': ''},
				'a': {'before': '[{text}]({href}{title})', 'after': ''},
				'h1': {'before': '\n\n# ', 'after': '\n\n'},
				'h2': {'before': '\n\n## ', 'after': '##\n\n'},
				'h3': {'before': '\n\n### ', 'after': '\n\n'},
				'h4': {'before': '\n\n#### ', 'after': '\n\n'},
				'h5': {'before': '\n\n##### ', 'after': '\n\n'},
				'h6': {'before': '\n\n###### ', 'after': '\n\n'},
				'ul': {'before': '\n\n', 'after': '\n\n'},
				'ol': {'before': '\n\n', 'after': '\n\n'},
				'li': {'before': '{prefix}   ', 'after': '\n'},
				'strong': {'before': '__', 'after': '__'},
				'b': {'before': '__', 'after': '__'},
				'em': {'before': '_', 'after': '_'},
				'i': {'before': '_', 'after': '_'}
			}
		return conversion_mapping
			

	def _process_tag(self, tag, before=None, after=None, unwrap=False):
		if (before != None):
			tag.insert_before(before)
		if (after != None):
			tag.insert_after(after)
		if (unwrap != None):
			tag.unwrap()
	
	
	def _process_block(self, tag):
		self._process_tag(tag, '\n\n','\n\n', True)

	def _process_ignorable(self, tag):
		tag.string = ""
		tag.unwrap()
		
	def _process_block_keep_name(self, tag):
		self._process_tag(tag, '\n\n' + tag.name,'\n\n', True)	

	def _process_comment(self, tag):
		self._process_tag(tag, '<!--- ' + tag.name + ': ', ' -->', True)
			
	def _process_blockquote(self, tag):
		# Processing logic for blockquote tag
		self._process_tag(tag, '<<<BLOCKQUOTE: ', '>>>', True)
		
	def _process_a(self, tag):
		# Processing logic for a tag
		for child in tag.find_all(recursive=False):
			self._messy_markdownify(child)
		if not tag.has_attr('href'):
			return
		if tag.string != tag.get('href') or tag.has_attr('title'):
			title = ''
			if tag.has_attr('title'):
				title = ' "%s"' % tag['title']
			tag.string = '[%s](%s%s)' % (BeautifulSoup(unicode(tag), 'html.parser').string,
										tag.get('href', ''),
										title)
		else:
			tag.string = '<<<FLOATING LINK: %s>>>' % tag.string
		tag.unwrap()

	def _process_h(self, tag):
		# Processing logic for headings 
		level = int(tag.name[1])
		self._process_tag(tag,'\n\n%s ' % ('#' * level), '\n\n', True)
	
	
	def _process_li(self, tag, _listType, _listIndex):
		if not _listType:
			return
		if _listType == 'ul':
			tag.insert_before('*   ')
		else:
			tag.insert_before('%d.   ' % _listIndex)
		
		for c in tag.contents:
			if type(c) != element.NavigableString:
				continue
			c.replace_with('\n    '.join(c.split('\n')))
		tag.insert_after('\n')
		tag.unwrap()


	def _process_img(self, tag):
		# Processing logic for img tag
		alt = ''
		title = ''
		if tag.has_attr('alt'):
			alt = tag['alt']
		if tag.has_attr('title') and tag['title']:
			title = ' "%s"' % tag['title']
		tag.string = '![%s](%s%s)' % (alt, tag['src'], title)
		tag.unwrap()


	def _process_pre(self, tag):
		# Processing logic for pre tag
		tag.insert_before('\n\n')
		tag.insert_after('\n\n')
		if tag.code:
			if not _supportedAttrs(tag.code):
				return
			for child in tag.code.find_all(recursive=False):
				if child.name != 'br':
					return
			for br in tag.code.find_all('br'):
				br.string = '\n'
				br.unwrap()
			tag.code.unwrap()
			lines = unicode(tag).strip().split('\n')
			lines[0] = lines[0][5:]
			lines[-1] = lines[-1][:-6]
			if not lines[-1]:
				lines.pop()
			for i,line in enumerate(lines):
				line = line.replace(u'\xa0', ' ')
				lines[i] = '    %s' % line
			tag.replace_with(BeautifulSoup('\n'.join(lines), 'html.parser'))


	def _process_code(self, tag):
		if tag.find_all(recursive=False):
			return
		self._process_tag(tag, '`` ', ' ``', True)


	def _process_p(self, tag, _blockQuote):
		if tag.name == 'p':
			if tag.string != None:
				if tag.string.strip() == u'':
					tag.string = u'\xa0'
					tag.unwrap()
					return
			if not _blockQuote:
				tag.insert_before('\n\n')
				tag.insert_after('\n\n')
			else:
				tag.insert_before('\n')
				tag.insert_after('\n')
			tag.unwrap()

  
	def _messy_markdownify(self, tag, _listType=None, _blockQuote=False, _listIndex=1):
		"""Recursively converts html tags into markdown"""
		children = tag.find_all(recursive=False)
	
		if tag.name == '[document]':
			for child in children:
				self._messy_markdownify(child, _listType, _blockQuote, _listIndex)
			return

		if tag.name not in self.tag_processors or not _supportedAttrs(tag):
			if tag.name not in self.inlineTags:
				tag.insert_before('\n\n')
				tag.insert_after('\n\n')
			else:
				_escapeCharacters(tag)
				for child in children:
					self._messy_markdownify(child)
				
		if tag.name not in ('pre', 'code'):
			_escapeCharacters(tag)
			_breakRemNewlines(tag)

		
		# Handle cases where we need to pass parameters into the tag processors
		if tag.name == 'li':
			self.tag_processors[tag.name](tag, _listType, _listIndex)
		elif tag.name == 'p':
			self.tag_processors[tag.name](tag, _blockQuote)
		elif tag.name in self.tag_processors:
			# run the processors and pass through any arguments
			self.tag_processors[tag.name](tag)

		if tag.name in {'ol', 'ul'}:
			_listType = tag.name
		
		# handle ordered lists slightly, do an early return
		if tag.name in {'ol'}:
			i = 0 
			for child in children:
				self._messy_markdownify(child, 'ol', _blockQuote, i+1)
				i = i+1
			
			return 
		
		for child in children:
			self._messy_markdownify(child, _listType, _blockQuote, _listIndex)

	
	def convert_to_messy(self, html):
		"""converts an html string to markdown while preserving unsupported markup."""
		# borrows heavily from the html2markdown library
		soup = BeautifulSoup(html, 'html.parser')
		
		# Strip out doctype 
		# TO-DO: do it at the start
		for item in soup.contents:
			if isinstance(item, Doctype):
				item.extract()
	
		# Remove script tags and their content
		[x.decompose() for x in soup.find_all('script')]
	   
		self._messy_markdownify(soup)

		# Brought in from parent module (?)
		ret = unicode(soup).replace(u'\xa0', '&nbsp;')
		ret = re.sub(r'\n{3,}', r'\n\n', ret)
		# ! FIXME: hack
		ret = re.sub(r'&lt;&lt;&lt;FLOATING LINK: (.+)&gt;&gt;&gt;', r'<\1>', ret)
		# ! FIXME: hack
		sp = re.split(r'(&lt;&lt;&lt;BLOCKQUOTE: .*?&gt;&gt;&gt;)', ret, flags=re.DOTALL)
		for i,e in enumerate(sp):
			if e[:len('&lt;&lt;&lt;BLOCKQUOTE:')] == '&lt;&lt;&lt;BLOCKQUOTE:':
				sp[i] = '> ' + e[len('&lt;&lt;&lt;BLOCKQUOTE:') : -len('&gt;&gt;&gt;')]
				sp[i] = sp[i].replace('\n', '\n> ')
		ret = ''.join(sp)
		return ret.strip('\n')


# If the script is being run directly
if __name__ == "__main__":
	converter = HTMLToMarkdownConverter()
	#print(Converter.convert_to_messy( '<ol><li>Test</li></ol>'))	
	#print(Converter.convert_to_messy( '<ol><li>Test</li><li><code>Here is some code</code></li></ol>'))
	print(converter.convert_to_messy('<html><h2>Test</h2><pre><code>Here is some code</code></pre></html>'))

   