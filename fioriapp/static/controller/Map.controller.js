sap.ui.define([
	"sap/ui/demo/basicTemplate/controller/App.controller"
], function (AppController) {
	"use strict";

	var self;
	var mapId;
	var renewableMarkers;

	return AppController.extend("sap.ui.demo.basicTemplate.controller.Map", {

		/**
		 * Called when a controller is instantiated and its View controls (if available) are already created.
		 * Can be used to modify the View before it is displayed, to bind event handlers and do other one-time initialization.
		 * @memberOf com.delta.view.App
		 */

		onInit: function() {
			this.getView().byId("titleText").setText("Map");
			self = this;
			mapId = this.getView().byId("map_canvas_full").sId;
			this.doLog();
			this.getRouter().getRoute("Map").attachPatternMatched(this._onObjectMatched, this);

			console.log(self.getMapData());

		},

		_onObjectMatched: function() {

			setTimeout(function() {
				self.map.invalidateSize();
			}, 500);

		},

		onAfterRendering: function() {

			/* Create Leaflet Map and set up markers layers */
			var tiles = L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/light-v9/tiles/256/{z}/{x}/{y}?access_token={accessToken}', {
				maxZoom: 20,
				attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
				accessToken: 'pk.eyJ1IjoibmlhbGxtY2NhYmUiLCJhIjoiY2plMnhwZTVjMjVjNDJxbzY4bW0zZ3RsdSJ9.LHcaHH57UShwertKSguG6A'
			}),

			latlng = L.latLng(53.5642418,-1.4833096);
			this.map = L.map(mapId, {
				center: latlng,
				zoom: 10,
				layers: [tiles]
			});

			this.map.invalidateSize();

			renewableMarkers =  L.markerClusterGroup({
				spiderfyOnMaxZoom: true,
				showCoverageOnHover: true,
				zoomToBoundsOnClick: true
			});

			var lats = self.getMapData();
			lats = lats.d.results;

			for(var i in lats) {
				var circle = L.circleMarker( [lats[i].LATITUDE, lats[i].LONGITUDE], {
					fillColor:'#f39c12',
					fillOpacity: 0.6,
					stroke: false
				});

				var popup = L.popup()
				    .setContent('<p>UPRN: '+lats[i].UPRN+'<br />SURNAME: '+lats[i].CHILD_SURNAME+'</p>');
				circle.bindPopup(popup).openPopup();

				renewableMarkers.addLayer(circle);
			}


			self.addMarkers();
		},

		removeMarkers: function() {
			this.map.removeLayer(renewableMarkers);
		},

		addMarkers: function() {
			this.map.addLayer(renewableMarkers);
		}

	});
});