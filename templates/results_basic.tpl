%#template to generate a HTML table from a list of tuples (or list of lists, or tuple of tuples or ...)
<p>Search results:
<p>
	<table>
	%for trip in data:
		%for seg in trip:
			%segstr = seg.condensed_repr()
		  <tr>
		    <td>{{segstr}}</td>
		  </tr>
		%end
		<tr><td>----------</td></tr>
	%end
	</table>
<hr width=40% align=left>
<p><a href="/ual">Back</a></p>
