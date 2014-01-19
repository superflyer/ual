  <head>
  	<title>SuperFlyer Mobile</title>
  	<link href="static/superflyer.css" type="text/css" rel="stylesheet"/>
  	
  	
  	<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
  	
  	<meta name="format-detection" content="telephone=no">
  	
  	
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
			
				Find Availability
			
		</div>
		<div id="subHeaderContent">
			
		</div>
	</div>
	
	<div id="errorContainer" class="info-message">
		
	</div>
	
 	<div id="content">
		
	<form action="/searchresults" name="awardUpgrade" method="post">

		<div class="form-group">
   			<table>
   				<tr>
    				<td>From<span class="required"></span></td>
					<td><input type="text" required="true" name="departAirport" value="{{params.depart_airport if params else ''}}" autocorrect="off" placeholder="3 letter airport code" maxlength="3" /></td>
    			</tr>
    			<tr>
    				<td>To<span class="required"></span></td>
					<td><input type="text" required="true" name="arriveAirport" value="{{params.arrive_airport if params else ''}}" autocorrect="off" maxlength="3" /></td>
    			</tr>
    			<tr>
    				<td>Depart<span class="required"></span></td>
    				<td>
				    	
				    		
				    	<input type="number" pattern="[0-9]*" name="departMonth" value="{{params.depart_datetime.month if params else today.month}}" class="date-input" size="3" maxlength="2" placeholder="mm" required="true"/> /
				    	<input type="number" pattern="[0-9]*" name="departDay" value="{{params.depart_datetime.day if params else today.day}}" class="date-input" size="3" maxlength="2" placeholder="dd" required="true"/> 
				    		
				        
				    </td>
				</tr>
    		</table>
    	</div>
    	

		<div class="form-group">
   			<table>
   				<tr>
					<td align=center><input type="checkbox" name="classCodeO" value="O" {{'checked' if params and 'O' in params.buckets else ''}}></td>
    				<td><span>First - Saver Award (O)</span></td>			    			
				</tr>
   				<tr>
					<td align=center><input type="checkbox" name="classCodeI" value="I" {{'checked' if params and 'I' in params.buckets else ''}}></td>
    				<td><span>Business - Saver Award (I/IN)</span></td>			    			
				</tr>
   				<tr>
					<td align=center><input type="checkbox" name="classCodeR" value="R" {{'checked' if params and 'R' in params.buckets else ''}}></td>
    				<td><span>Business - Upgrade (R/RN)</span></td>			    			
				</tr>
   				<tr>
					<td align=center><input type="checkbox" name="classCodeX" value="X" {{'checked' if params and 'X' in params.buckets else ''}}></td>
    				<td><span>Coach - Saver Award (X/XN)</span></td>			    			
				</tr>
    			<tr>
					<td align=center><input type="checkbox" name="otherCheck" value="True" {{'checked' if params and params.other_buckets() else ''}}></td>
    				<td>Other: <input type="text" size=20 name="otherClassCodes" value="{{params.other_buckets() if params else ''}}" autocorrect="off"/></td>
    			</tr>
   				<tr>
					<td align=center><input type="checkbox" name="allClasses" value="True" {{'checked' if params and not params.buckets else ''}}></td>
    				<td><span>All booking codes</span></td>			    			
				</tr>
    		</table>
    	</div>



	    
		<div class="form-group">
    		<table>
    			<tr>
    				<td>Airline</td>
    				<td>
    					<select name="airlineCode">
    						
					        	<option value="UA" Selected='Selected' >United - UA</option>
					        	<option value="AC"  >Air Canada - AC</option>
					        	<option value="NK"  >ANA - NH</option>
				       			<option value="SN"  >Brussels Airlines - SN</option>
					        	<option value="LH"  >Lufthansa - LH</option>
					        	<option value="LX"  >SWISS - LX</option>
					        	<option value="TK"  >Turkish Airlines - TK</option>
				            
				            
    					</select>
    				</td>
    			</tr>
    			<tr>
    				<td>Flight No.</td>
					<td><input type="number" pattern="[0-9]*" name="flightNumber" value="" autocorrect="off" /></td>
				</tr>
   				<tr>
    				<td><span>Nonstop</span></td>			    			
					<td><input type="checkbox" name="nonstop" value="True" {{'checked' if params and params.nonstop else ''}}></td>
				</tr>

		   	</table>
		</div>
		
		<div class="button-container">
			<input type="image" src="static/button-submit.png" alt="Submit">
		</div>

<!--    	<div class="button-container">
    		<input type="submit" name="search" class="button search" value="Search" />
		</div>
	</form>  
  
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
	
	
		
	
		
		
	

  </body>
</html>
