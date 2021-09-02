import pickle as pkl

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()

stopword_add=['category', 'redirect', 'ref', 'gallery', 'timeline', 'noinclude', 'pre', 'table', 'tr', 'td',
            'ul', 'li', 'ol', 'dl', 'dt', 'dd', 'menu', 'dir', 'nowiki', 'cite', 'source', 'hiero', 'div', 'font', 'span', 'strong',
            'strike', 'blockquote', 'tt', 'var', 'sup', 'sub', 'big', 'small', 'center', 'h1', 'h2', 'h3', 'em', 
            'b', 'i', 'u', 'a', 's', 'p', 'references', 'ref', 'img', 'br', 'hr', 'li', 'dt', 'dd', 'nbsp', 
            'iexcl', 'cent', 'pound', 'curren', 'yen', 'brvbar', 'sect', 'uml', 'copy', 'ordf', 'laquo', 'not', 'shy',
            'reg', 'macr', 'deg', 'plusmn', 'sup2', 'sup3', 'acute', 'micro', 'para', 'middot', 'cedil', 'sup1', 'ordm', 
            'raquo', 'frac14', 'frac12', 'frac34', 'iquest', 'agrave', 'aacute', 'acirc', 'atilde', 'auml', 'aring', 'aelig', 
            'ccedil', 'egrave', 'eacute', 'ecirc', 'euml', 'igrave', 'iacute', 'icirc', 'iuml', 'eth', 'ntilde',
            'ograve', 'oacute', 'ocirc', 'otilde', 'ouml', 'times', 'oslash', 'ugrave', 'uacute', 'ucirc', 'uuml', 'yacute', 
            'thorn', 'szlig', 'agrave', 'aacute', 'acirc', 'atilde', 'auml', 'aring', 'aelig', 'ccedil', 'egrave', 'eacute', 
            'ecirc', 'euml', 'igrave', 'iacute', 'icirc', 'iuml', 'eth', 'ntilde', 'ograve', 'oacute', 'ocirc', 'otilde', 
            'ouml', 'divide', 'oslash', 'ugrave', 'uacute', 'ucirc', 'uuml', 'yacute', 'thorn', 'yuml', 'fnof', 'alpha', 
            'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 
            'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega', 'alpha', 'beta', 'gamma', 
            'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 
            'rho', 'sigmaf', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega', 'thetasym', 'upsih', 'piv', 'bull', 
            'hellip', 'prime', 'Prime', 'oline', 'frasl', 'weierp', 'image', 'real', 'trade', 'alefsym', 'larr', 'uarr', 
            'rarr', 'darr', 'harr', 'crarr', 'larr', 'uarr', 'rarr', 'darr', 'harr', 'forall', 'part', 'exist', 'empty', 
            'nabla', 'isin', 'notin', 'ni', 'prod', 'sum', 'minus', 'lowast', 'radic', 'prop', 'infin', 'ang', 'and', 
            'or', 'cap', 'cup', 'int', 'there4', 'sim', 'cong', 'asymp', 'ne', 'equiv', 'le', 'ge', 'sub', 'sup',
            'nsub', 'sube', 'supe', 'oplus', 'otimes', 'perp', 'sdot', 'lceil', 'rceil', 'lfloor', 'rfloor', 'lang',
            'rang', 'loz', 'spades', 'clubs', 'hearts', 'diams', 'quot', 'lt', 'gt', 'oelig', 'oelig', 'scaron', 
            'scaron', 'Yuml', 'circ', 'tilde', 'ensp', 'emsp', 'thinsp', 'zwnj', 'zwj', 'lrm', 'rlm', 'ndash', 
            'mdash', 'lsquo', 'rsquo', 'sbquo', 'ldquo', 'rdquo', 'bdquo', 'dagger', 'Dagger', 'permil', 'lsaquo', 'rsaquo', 'euro']

for i in range(len(stopword_add)):
    stopword_set.add(stopword_add[i])

print(len(stopword_set))
with open('stopwords.pkl', 'wb') as f:
    pkl.dump(set(stopword_set), f)
    f.close()