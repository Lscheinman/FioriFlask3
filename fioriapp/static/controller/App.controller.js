sap.ui.define([
	"sap/ui/core/mvc/Controller",
	"../model/formatter",
	"sap/ui/core/routing/History"
], function(Controller, formatter, History) {
	"use strict";

	var self;
	var mapId;
	var novStatus = [
		"#f39c12",
		"#f39c12",
		"#f39c12",
		"#f39c12",
		"#f39c12",
		"#27ae60",
		"#27ae60",
		"#f39c12",
		"#c0392b",
		"#f39c12",
		"#f39c12",
		"#c0392b",
		"#f39c12",
		"#27ae60",
		"#27ae60"
	];
	var octStatus = [
		"#27ae60",
		"#27ae60",
		"#c0392b",
		"#27ae60",
		"#c0392b",
		"#27ae60",
		"#c0392b",
		"#c0392b",
		"#f39c12",
		"#27ae60",
		"#f39c12",
		"#c0392b",
		"#c0392b",
		"#f39c12",
		"#27ae60",
		"#f39c12"
	];
	// Markers
	var renewableMarkers;

	return Controller.extend("sap.ui.demo.basicTemplate.controller.App", {

		formatter: formatter,

		onInit: function () {

		    self = this;

		},
		press: function(tile) {

			var selectedData = {};
			sap.ui.core.BusyIndicator.show(0);
			this.getRouteData(tile).done(function(result) {
				var oModel = new sap.ui.model.json.JSONModel(result.d);
				sap.ui.getCore().setModel(oModel, tile + "Model");
				self.routeToApp(tile);

			}).fail(function(result) {
				console.log(result);
				sap.ui.core.BusyIndicator.hide();
				MessageToast.show(result.d);
			});

			mapId = this.getView().byId("map_canvas").sId;

		},
		onNavBack: function() {

			var sPreviousHash = History.getInstance().getPreviousHash();

			if (sPreviousHash !== undefined) {
				history.go(-1);
			} else {
				this.getRouter().navTo("home", {}, true);
			}

		},

		getRouteData: function(url){
			return jQuery.ajax({
				url: url,
				type: "GET"
			});
		},

		getRouter : function () {
			return sap.ui.core.UIComponent.getRouterFor(this);
		},

		routeToApp: function(tile) {
			self.getRouter().navTo(tile, {});
			sap.ui.core.BusyIndicator.hide();

		},
	});
});