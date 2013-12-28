  <head>
  	<title>SuperFlyer Mobile</title>
  	<link href="static/superflyer.css" type="text/css" rel="stylesheet"/>
  	<script type="text/javascript" src="/static/superflyer.js?v=null"></script>
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
				Flight Availability
		</div>
		<div id="subHeaderContent">
  		<div>
			{{params.depart_airport.upper()}} to {{params.arrive_airport.upper()}} on {{params.depart_date}}
		</div>
		<div>
					Flying
					<b>UA  </b>
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
	<form action="/mobile/flightAvailabilityResults.do" method="post" name="flightAvailabilityResultsForm">
						% for trip in data:
						<div class="form-result">
							<span class="form-results-expanded-state">Expanded</span>
								% for seg in trip:
								<div class="form-results-overview">
									<table>
										<tr>
											<td class="description">{{seg.flightno}}</td>
											<td class="info">
												{{seg.depart_airport}} {{seg.depart_time}} &rarr; {{seg.arrive_airport}} {{seg.arrive_time}}
												<div class="info-subheader">{{seg.search_results if seg.search_results else seg.availability}} 
												</div>
											</td>
										</tr>
									</table>
								</div>
								<div class="form-results-details">
									<table>
										<tr>
											<td class="description"></td>
											<td class="info"><label>Stops: </label>0</td>
										</tr>
										<tr>
											<td class="description"></td>
											<td class="info"><label>Aircraft: </label>{{seg.aircraft}}</td>
										</tr>
										<tr>
											<td class="description"></td>
											<td class="info"><label>Frequency: </label>M,T,W</td>
										</tr>
										<tr>
											<td class="description"></td>
											<td class="info"><label>Reliability: </label>100% / 8m</td>
										</tr>
										<tr>
											<td colspan="2">
												<div class="links">
													<a href="flightDetails.do?airlineCode=UA&flightNumber=1038&departDate=12/24/13&passthrough=true">Flight Details</a> &middot;
															<a href="seatMap.do?airlineCode=UA&flightNumber=1038&departDate=12/24/13&departingAirportCode=SFO&arrivingAirportCode=LAX&refine=true">Seat Map</a>  &middot;
													<a href="createFlightAlert.do?departingAirportCode=SFO&arrivingAirportCode=LAX&departDate=12/24/13&departTimestamp=12/24/13 6:19 AM&departTimeZone=PST&airlineCode=UA&flightNumber=1038&pos=&refine=true">Create Alert</a>
												</div>
											</td>
										</tr>
									</table>
								</div>
								% end
						</div>
						% end
		<ul class="menu">
			<li><a href="flightAvailability.do"><span>New Search</span></a></li>
			<li><a href="flightAvailability.do?departingAirportCode=SFO&arrivingAirportCode=SAN&departDate=12/24/13&departTime=12:00 AM&connectingAirport1Code=&connectingAirport2Code=&airline1Code=UA&airline2Code=&airline3Code=&classCodes=&connectionPref=&pos=&allianceCode=&excludeCodeshares=false&refine=true"><span>Refine Search</span></a></li>
				<li><a href="flightAvailability.do?departingAirportCode=SAN&arrivingAirportCode=SFO&connectingAirport1Code=&connectingAirport2Code=&airline1Code=UA&airline2Code=&airline3Code=&classCodes=&connectionPref=&pos=&allianceCode=&excludeCodeshares=false&refine=true"><span>Refine Search for Return Availability (SAN-SFO)</span></a></li>
			<li><a href="fareInformation.do?departingAirportCode=SFO&arrivingAirportCode=SAN&departDate=12/24/13&passthrough=true"><span>View fares from SFO to SAN</span></a></li>
				<li><a href="fareInformation.do?departingAirportCode=SFO&arrivingAirportCode=SAN&departDate=12/24/13&airline1Code=UA&airline2Code=&airline3Code=&classCodes=&passthrough=true"><span>View fares from SFO to SAN on UA  </span></a></li>
				 
				<li><a href="awardUpgrade.do?departingAirportCode=SFO&arrivingAirportCode=SAN&departDate=12/24/13&departTime=12:00 AM&connectingAirport1Code=&connectingAirport2Code=&airlineCode=UA&connectionPref=&allianceCode=&refine=true&next=true"><span>Search for Awards & Upgrades for SFO to SAN on UA</span></a></li>
		</ul>
	</form>  
  
	</div>
	<div id="footer" align="center">
				<a href="main.do">Home</a> &middot;
				<a href="logout.do">Log Out</a> <br />
			<a href="contactUs.do">Contact Us</a> &middot; 
			<a href="faq.do">Help</a> &middot; <a href="terms.do">Terms</a> &middot; <a href="privacyPolicy.do">Privacy Policy</a> 
				&middot; <a href="#viewDesktop" id="viewDesktopVersion">Desktop Version</a>
		<br/>
		&copy;2004-2013 Expert Travel Services, LLC
	</div>
	<script type="text/javascript">
		var urlToNavigateTo = ""; 
		var elements1 = YAHOO.util.Dom.getElementsByClassName("form-results-expanded-state", "span", "content");
		var elements2 = YAHOO.util.Dom.getElementsByClassName("expandable", "div", "content");
		var elements = elements1.concat(elements2);
		YAHOO.util.Event.addListener(elements, "click", function(event){
			var target = YAHOO.util.Event.getTarget(event);
			if(YAHOO.util.Dom.hasClass(target, "form-results-expanded-state")||YAHOO.util.Dom.hasClass(target, "expandable")) {
				if(YAHOO.util.Dom.hasClass(target.parentNode, "expanded")){
					YAHOO.util.Dom.removeClass(target.parentNode, "expanded");
				}
				else{
					YAHOO.util.Dom.addClass(target.parentNode, "expanded");
				}
			}
		});
		GUI.on("viewDesktopVersion", "click", function(event){
			YAHOO.util.Event.stopEvent( event );
			YAHOO.util.Cookie.set("mobilePref", "ViewDesktop", {
			    path: "/",
			    expires: new Date("January 12, 2900")
			});
			window.location.href='https://www.expertflyer.com/';
		}, this, true);   
		if("true" == "true" && ("3" == 4 || "3" == 2)){
			var mobileAppCookie = YAHOO.util.Cookie.get("mobileApp");
			if( (null == mobileAppCookie) && (navigator.userAgent.match(/iPhone/i) || navigator.userAgent.match(/iPod/i) || navigator.userAgent.match(/iPad/i) || navigator.userAgent.match(/Android/i)) ){
				if(navigator.userAgent.match(/Android/i)){
					GUI.show("mobileAppAndroidBanner");
				}
				else{
					GUI.show("mobileAppItunesBanner");
				}
				GUI.show("mobileAppBanner");
			}
			GUI.on("bannerNoThanks", "click", function(event){
				YAHOO.util.Event.stopEvent( event );
				YAHOO.util.Cookie.set("mobileApp", "noThanks", {
				    path: "/",
				    expires: new Date("January 12, 2900")
				});
				GUI.hide("mobileAppBanner");
			}, this, true);   
		}
		function getUrlFunction(){
			return "getUrl";
		}
		function setUrlNative(url){
			urlToNavigateTo	= url;	
			return false;
		};
		function getUrl(){
			var temp = "";
			if(urlToNavigateTo){
				temp = urlToNavigateTo;
				urlToNavigateTo = "";
			}
			return temp;
		};
		GUI.util.load( function() {
			if("" >= 1.3){
				var nativeLinks = YAHOO.util.Dom.getElementsByClassName("native-url-link", "a", "content");
				YAHOO.util.Event.addListener(nativeLinks, "click", function(event){
					YAHOO.util.Event.stopEvent( event );
					var target = YAHOO.util.Event.getTarget(event);
					setUrlNative(target.href);
				});
			}
		});
	</script>
		<script type="text/javascript">
		</script>
  
  </body>
</html>
