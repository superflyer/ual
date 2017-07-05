  <head>
  	<title>SuperFlyer Mobile</title>
  	<link href="static/superflyer.css" type="text/css" rel="stylesheet"/>
  	<script type="text/javascript" src="/static/superflyer.js?v=null"></script>

	<script type="text/javascript">
		function searchPrev() {
			document.previousDay.submit();
		}
		function searchNext() {
			document.nextDay.submit();
		}
	</script>

	<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
  	
  	<meta name="format-detection" content="telephone=no">
  	
       <style type="text/css">
		    
		    #availabilityCodesContiner{
		    	padding-left:7px;
		    }
		    
		    #availabilityCodesContiner h3,
		    #availabilityCodesContiner label{
		    	font-weight:bold;
		    }
       		
       </style>
  
  	
  	<style>
  		#mobileAppBanner{
  			color: white;
			padding: 14px;
			font-weight: bold;
			background-color: #3062A1;
			font-size: 17px;
  		}
  		#mobileAppBanner a.yes-please{
  			text-decoration: none;
			text-align: center;
			color: white;
			font-weight: bold;
			display: block;
			box-shadow: black 0px 2px 2px;
			background: -webkit-gradient(linear, left top, left bottom, from(#2F4158), to(#253141));
			padding: 20px;
			border-radius: 15px;
			border: 1px solid #1F2A39;
			margin-top:10px;
  		}
  		#mobileAppBanner a.no-thanks{
  			float: right;
			margin-top: 20px;
			text-decoration: none;
			color: #DDD;
			font-size: smaller;
			cursor: pointer;
			font-weight:bold;
  		}
  		.clear{
  			clear:both;
  		}
  		#mobileAppAndroidBanner,
  		#mobileAppItunesBanner{
  			display:none;
  		}
  	</style>
  </head>
  
  <body>
  
	<div id="subHeader">
		<div id="subHeaderTitle">
			{{params.depart_airport.upper()}} to {{params.arrive_airport.upper()}} 
			on {{params.depart_datetime.strftime('%a')}} 
			{{params.depart_datetime.strftime('%m/%d/%y').strip('0')}}
		</div>
		<div id="subHeaderContent">
  		<div>
		</div>
		<div>
					<!-- Flying <b>UA </b> -->
					{{'Nonstop' if params.nonstop else ''}}
		</div>
		<div>
		</div>
		<div>
		</div>
		<div>
		</div>
		<div>
		</div>
  
		</div>
	</div>
	<div id="errorContainer" class="info-message">
	</div>
 	<div id="content">
	<!-- <form action="/mobile/flightAvailabilityResults.do" method="post" name="flightAvailabilityResultsForm"> -->
			% for trip in data:
			<div class="form-result">
				<span class="form-results-expanded-state">Expanded</span>
					% for seg in trip:
					<div class="form-results-overview">
						<table>
							<tr>
								<td class="description">{{seg.flightno}}
									<div class="info-subheader">
									{{seg.aircraft}}
									</div>
								</td>
								<td class="info">
									{{seg.depart_airport}} 
									{{seg.depart_datetime.strftime('%H:%M')+seg.depart_offset}} &rarr; 
									{{seg.arrive_airport}} {{seg.arrive_datetime.strftime('%H:%M')+seg.arrive_offset}}
									<div class="info-subheader">{{seg.bucket_repr()}} 
									</div>
								</td>
							</tr>
						</table>
					</div>
					% end
			</div>
			% end

		<form action="/searchresults" name="previousDay" method="post">
			<input type="hidden" name="departAirport" value={{params.depart_airport.upper()}}>
			<input type="hidden" name="arriveAirport" value={{params.arrive_airport.upper()}}>
			<input type="hidden" name="departMonth" 
				value={{(params.depart_datetime + params.timedelta(days=-1)).strftime('%m')}}>
			<input type="hidden" name="departDay" 
				value={{(params.depart_datetime + params.timedelta(days=-1)).strftime('%d')}}>
			<input type="hidden" name="airlineCode" value="UA">
			<input type="hidden" name="flightNumber" value={{params.flightno}}>
			<input type="hidden" name="nonstop" value={{params.nonstop if params.nonstop else False}}>
			<input type="hidden" name="otherCheck" value={{True if params.buckets else False}}>
			<input type="hidden" name="otherClassCodes" value={{params.buckets}}>
			<input type="hidden" name="all_classes" value={{True if not params.buckets else False}}>
		</form>

		<form action="/searchresults" name="nextDay" method="post">
			<input type="hidden" name="departAirport" value={{params.depart_airport.upper()}}>
			<input type="hidden" name="arriveAirport" value={{params.arrive_airport.upper()}}>
			<input type="hidden" name="departMonth" 
				value={{(params.depart_datetime + params.timedelta(days=1)).strftime('%m')}}>
			<input type="hidden" name="departDay" 
				value={{(params.depart_datetime + params.timedelta(days=1)).strftime('%d')}}>
			<input type="hidden" name="buckets" value={{params.buckets}}>
			<input type="hidden" name="airlineCode" value="UA">
			<input type="hidden" name="flightNumber" value={{params.flightno}}>
			<input type="hidden" name="nonstop" value={{params.nonstop if params.nonstop else False}}>
			<input type="hidden" name="otherCheck" value={{True if params.buckets else False}}>
			<input type="hidden" name="otherClassCodes" value={{params.buckets}}>
			<input type="hidden" name="all_classes" value={{True if not params.buckets else False}}>
		</form>

		<ul class="menu">
			<li><a href="/ual"><span>New Search</span></a></li>
			<li><a href="/ual?depart_airport={{params.depart_airport.upper()}}&arrive_airport={{params.arrive_airport.upper()}}&depart_date={{params.depart_date}}&buckets={{params.buckets}}&flightno={{params.flightno}}&nonstop={{params.nonstop if params.nonstop else ''}}&refine=true"><span>Refine Search</span></a></li>
			<li><a href="/ual?depart_airport={{params.arrive_airport.upper()}}&arrive_airport={{params.depart_airport.upper()}}&depart_date={{params.depart_date}}&buckets={{params.buckets}}&flightno={{params.flightno}}&nonstop={{params.nonstop if params.nonstop else ''}}&refine=true"><span>Refine Search for Return Availability ({{params.arrive_airport.upper()}}-{{params.depart_airport.upper()}})</span></a></li>
			<li><a href="javascript: searchPrev()"><span>Search Previous Day</span></a></li>
			<li><a href="javascript: searchNext()"><span>Search Next Day</span></a></li>
		</ul>
	<!-- </form>   -->
  
	</div>
	<div id="footer" align="center">
				&nbsp;
	</div>  
  </body>
</html>
