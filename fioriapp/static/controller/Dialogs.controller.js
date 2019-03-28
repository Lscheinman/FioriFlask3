sap.ui.define([
	"sap/ui/demo/basicTemplate/controller/App.controller",
	"sap/ui/model/Filter",
	"sap/ui/model/FilterOperator",
	"sap/ui/model/json/JSONModel",
	"sap/m/MessageToast",
	"sap/viz/ui5/data/FlattenedDataset",
	"sap/viz/ui5/controls/common/feeds/FeedItem",
	"sap/viz/ui5/format/ChartFormatter"
], function(AppController, Filter, FilterOperator, JSONModel, MessageToast, FlattenedDataset, FeedItem, ChartFormatter) {
	"use strict";

	var self;
	return AppController.extend("sap.ui.demo.basicTemplate.controller.Dialogs", {

		/* ============================================================ */
		/* Constants                                                    */
		/* ============================================================ */
		/**
		 * Constants used in the example.
		 *
		 * @private
		 * @property {String} sampleName Name of the chart container sample
		 * @property {Object} vizFrame Viz Frame used in the view
		 * @property {String} vizFrame.id Id of the Viz Frame
		 * @property {Object} vizFrame.dataset Config used for the Viz Frame Flattened data
		 * @property {Object[]} vizFrame.dataset.dimensions Flattened data dimensions
		 * @property {Object[]} vizFrame.dataset.measures Flattened data measures
		 * @property {Object} vizFrame.dataset.data Flattened data other config
		 * @property {Object} vizFrame.dataset.data.path Flattened data path
		 * @property {String} vizFrame.modulePath Path to the module's data
		 * @property {String} vizFrame.type Viz Frame Type
		 * @property {Object} vizFrame.properties Viz Frame properties
		 * @property {Object} vizFrame.properties.plotArea Viz Frame plot area property
		 * @property {Object} vizFrame.properties.plotArea.showGap Viz Frame plot area property
		 * @property {Object[]} vizFrame.feedItems Viz Frame feed items
		 */
		_constants: {
			sampleName: "sap.ui.demo.basicTemplate.ChartContainerSimpleToolbar",
			vizFrame: {
				id: "chartContainerVizFrame",
				dataset: {
					dimensions: [{
						name: 'Country',
						value: "{Country}"
					}],
					measures: [{
						group: 1,
						name: 'Profit',
						value: '{Revenue2}'
					}, {
						group: 1,
						name: 'Target',
						value: '{Target}'
					}, {
						group: 1,
						name: "Forcast",
						value: "{Forcast}"
					}, {
						group: 1,
						name: "Revenue",
						value: "{Revenue}"
					},
						{
							group: 1,
							name: 'Revenue2',
							value: '{Revenue2}'
						}, {
							group: 1,
							name: "Revenue3",
							value: "{Revenue3}"
						}],
					data: {
						path: "/Products"
					}
				},
				modulePath: "/",
				type: "line",
				properties: {
					plotArea: {
						showGap: true
					}
				},
				feedItems: [{
					'uid': "primaryValues",
					'type': "Measure",
					'values': ["Revenue"]
				}, {
					'uid': "axisLabels",
					'type': "Dimension",
					'values': ["Country"]
				}, {
					'uid': "targetValues",
					'type': "Measure",
					'values': ["Target"]
				}]
			}
		},

		onInit: function() {
            //TODO Add settings for other layouts
            //TODO buttons to switch layouts
            //TODO model to sequence graph updates and save versions
			this.oModelSettings = new JSONModel({
				maxIterations: 200,
				maxTime: 500,
				initialTemperature: 200,
				coolDownStep: 1
			});
			this.getView().setModel(this.oModelSettings, "settings");
			this.getView().setModel(sap.ui.getCore().getModel("DialogsModel"), "DialogsModel");
            //Initialize the Graph network
			this.oGraph = this.byId("graph");
			this.oGraph._fZoomLevel = 0.75;
			this.demoGraph();
			//Initialize the File Manager Integrated Menu
			this.oFilesTable = this.byId("idAvailableFiles");
			this.fillAvailableFiles();
			//Initialize the File Manager Upload Menu
			this.oUploadTable = this.byId("idUploadFiles");
			this.oUploadTable.setModel(new sap.ui.model.json.JSONModel({}));
			//Initialize Viz frame for charts
			var oVizFrame = this.getView().byId("chartContainerVizFrame");
			this.updateVizFrame(oVizFrame);

            var oVBI = new sap.ui.vbm.GeoMap({
                vos : [ new sap.ui.vbm.Spots({
                    items : [ new sap.ui.vbm.Spot({ position : "20;0;0" }) ]
                    }) ]
            });

            var DF = { Spots :
                [
                    { "value" : "8", "pos": "37.622882;55.755202;0",  "tooltip": "Moscow", "type":"Inactive"  },
                    { "value":  "23", "pos": "-74.013327;40.705395;0", "tooltip": "New York", "type":"Error"  },
                    { "value":  "2", "pos": "8.641568;49.293789;0", "tooltip": "SAP Walldorf", "type":"Success"  }
                ]
            };
            var DefaultPoints = new sap.ui.model.json.JSONModel();
            DefaultPoints.setData(DF);
            sap.ui.getCore().setModel(DefaultPoints, "DefaultPoints");
            var LaunchpadMap = this.byId("GeoMap");
            LaunchpadMap = new sap.ui.vbm.GeoMap();
            var oMapConfig = {
                "MapProvider": [{
                "name": "Open Street",
                "type": "",
                "description": "",
                "tileX": "256",
                "tileY": "256",
                "maxLOD": "20",
                "copyright": "OpenStreet",
                "Source": [
                    {
                    "id": "a",
                    "url" : "https://a.tile.openstreetmap.org/{LOD}/{X}/{Y}.png"
                    }
                ]
                }],
                    "MapLayerStacks": [{
                    "name": "Default",
                    "MapLayer": {
                    "name": "Default",
                    "refMapProvider": "Open Street Map",
                    "opacity": "1.0",
                    "colBkgnd": "RGB(255,255,255)"
                    }
                }]
            };
            LaunchpadMap.setMapConfiguration(oMapConfig);

		},
		/* ============================================================ */
		/* Helper Methods                                               */
		/* ============================================================ */
		/**
		 * Updated the Viz Frame in the view.
		 *
		 * @private
		 * @param {sap.viz.ui5.controls.VizFrame} vizFrame Viz Frame that needs to be updated
		 */
		updateVizFrame: function(vizFrame) {
			var oVizFrame = this._constants.vizFrame;
			var oModel = new JSONModel(sap.ui.getCore().getModel("DialogsModel").oData.demo_data.chart.d);
			var oDataset = new FlattenedDataset(oVizFrame.dataset);

			vizFrame.setVizProperties(oVizFrame.properties);
			vizFrame.setDataset(oDataset);
			vizFrame.setModel(oModel);
			this._addFeedItems(vizFrame, oVizFrame.feedItems);
			vizFrame.setVizType(oVizFrame.type);
		},
		/**
		 * Adds the passed feed items to the passed Viz Frame.
		 *
		 * @private
		 * @param {sap.viz.ui5.controls.VizFrame} vizFrame Viz Frame to add feed items to
		 * @param {Object[]} feedItems Feed items to add
		 */
		_addFeedItems: function(vizFrame, feedItems) {
			for (var i = 0; i < feedItems.length; i++) {
				vizFrame.addFeed(new FeedItem(feedItems[i]));
			}
		},

		createMonologue: function(sType) {

		    MessageToast.show("Creating a monologue");
		    sap.ui.core.BusyIndicator.show(0);
		    var oThis = this;
		    var oData = {
                'line': oThis.byId('Dialog.create_monologue.lines').getValue(),
                'tags': oThis.byId('Dialog.create_monologue.tags').getValue()
            };

		    jQuery.ajax({
				url: "/Dialogs/create_monologue",
				type: "POST",
                dataType : "json",
                async : true,
                data : oData,
                success : function(response){
                    MessageToast.show(response.data.message);
                    oThis.makeGraph(response.graph);
                    sap.ui.core.BusyIndicator.hide();
                },
                error: function(response){
                    console.log(response);
                }
			});
			console.log(sType);
		},

		createDialog: function(sType) {
            MessageToast.show("Creating a dialog");
            sap.ui.core.BusyIndicator.show(0);
            var oThis = this;
            var oData = {
                'nfrom': oThis.byId('Dialog.create_duo.from_input').getValue(),
                'nto': oThis.byId('Dialog.create_duo.to_input').getValue(),
                'tags': oThis.byId('Dialog.create_duo.tags').getValue()
            };

            jQuery.ajax({
				url: "/Dialogs/create_duo",
				type: "POST",
                dataType : "json",
                async : true,
                data : oData,
                success : function(response){
                    MessageToast.show(response.data.message);
                    oThis.makeGraph(response.graph);
                    sap.ui.core.BusyIndicator.hide();
                },
                error: function(response){
                    console.log(response);
                }
			});
			console.log(sType);
		},

		getResponse: function(sType) {
            MessageToast.show("Getting a response");
            sap.ui.core.BusyIndicator.show(0);
            var oThis = this;
            var oData = {
                'rtype': oThis.byId('Dialog.get_response.rtype').getSelectedItem().getKey(),
                'phrase': oThis.byId('Dialog.get_response.input').getValue(),
                'rel_text': oThis.byId('Dialog.get_response.tags').getValue()
            };

            jQuery.ajax({
                url : "/Dialogs/get_response",
                type : "POST",
                dataType : "json",
                async : true,
                data : oData,
                success : function(response){
                    MessageToast.show(response.data.message);
                    oThis.makeGraph(response.graph);
                    sap.ui.core.BusyIndicator.hide();
                },
                error: function(response){
                    console.log(response);
                }
			});

			console.log(sType);
		},

		updateGraph: function(oData, curModel){

            for (var i = 0; i < oData.nodes.length; i++){
                if(!((curModel.keys.indexOf(oData.nodes[i].attributes[2].value) > -1))){
                    curModel.oData.nodes.push(oData.nodes[i]);
                    curModel.keys.push(oData.nodes[i].attributes[2].value);
                }
		    }
		    for (var i = 0; i < oData.lines.length; i++){
                if(!((curModel.oData.lines.indexOf(oData.lines[i]) > -1))){
                    curModel.oData.lines.push(oData.lines[i]);
                }
		    }
		    var oModel = new JSONModel(curModel.oData);
		    oModel['keys'] = curModel.keys;
		    this.getView().setModel(oModel);
		},

		makeGraph: function(oData){
		    var curModel = this.getView().getModel();
		    //Iron man is in the demo graph so assume that we need to make the graph based on that
		    if(curModel.oData.nodes[0].title == "Iron Man"){
		        var oModel = new JSONModel(oData);
		        this.getView().setModel(oModel);
		        curModel = this.getView().getModel();
		        curModel['keys'] = oData.keys;
		        this.getView().setModel(curModel);
		    }
		    else{
		        this.updateGraph(oData, curModel);
		    }
		},

		demoGraph: function(){
            var oData = sap.ui.getCore().getModel("DialogsModel").oData.demo_data.network.d;
		    var oModel = new JSONModel(oData);
		    this.getView().setModel(oModel);

		},

		fillAvailableFiles: function(){
		    var oData = sap.ui.getCore().getModel("DialogsModel").oData.files;
		    var oModel = new JSONModel(oData);
		    this.oFilesTable.setModel(oModel);
		},

		removeMarkers: function() {
			this.map.removeLayer(renewableMarkers);
		},

		openMap: function() {
			self.getRouter().navTo("Map", {});
		},

		onDialogPress: function() {

			var dialog = new sap.m.Dialog({
				title: "Upload File",
				content: sap.ui.xmlfragment("sap.ui.demo.basicTemplate.view.Fragments.Upload", this),
				endButton: new sap.m.Button({
					text: "Close",
					press: function() {
						dialog.close();
					}
				}),
				afterClose: function() {
					dialog.destroy();
				}

			});
			this.getView().addDependent(dialog);
			dialog.open();

		},
		handleUploadComplete: function(oEvent) {
			var sResponse = oEvent.getParameter("response");
			var jResponse = sResponse.replace('<pre style="word-wrap: break-word; white-space: pre-wrap;">', '').replace('</pre>', '');
			jResponse = JSON.parse(jResponse);
			if (jResponse) {
				var sMsg = "";
				if (jResponse.status == 200) {
				    this.oUploadTable.setModel(new sap.ui.model.json.JSONModel(jResponse.data));
					oEvent.getSource().setValue("");
					sMsg = 'Upload complete'
				} else {
					sMsg = "Upload error";
				}
				MessageToast.show(sMsg);
			}
		},

		handleUploadPress: function(oEvent) {
			var oFileUploader = this.byId("fileUploader");
			if (!oFileUploader.getValue()) {
				MessageToast.show("Choose a file first");
				return;
			}
			oFileUploader.upload();
		},

		handleTypeMissmatch: function(oEvent) {
			var aFileTypes = oEvent.getSource().getFileType();
			jQuery.each(aFileTypes, function(key, value) {aFileTypes[key] = "*." +  value;});
			var sSupportedFileTypes = aFileTypes.join(", ");
			MessageToast.show("The file type *." + oEvent.getParameter("fileType") +
									" is not supported. Choose one of the following types: " +
									sSupportedFileTypes);
		},

		handleValueChange: function(oEvent) {
			MessageToast.show("Press the upload arrow to upload " +
									oEvent.getParameter("newValue"));
		},

		processUploadedFile: function(oEvent) {
		    var oData = {'filename': oEvent.getSource().getBindingContext().getObject().filename };

		    jQuery.ajax({
				url: "/Dialogs/process_file",
				type: "POST",
                dataType : "json",
                async : true,
                data : oData,
                success : function(response){
                    MessageToast.show(response.data.message);
                    oThis.makeGraph(response.graph);
                    sap.ui.core.BusyIndicator.hide();
                },
                error: function(response){
                    console.log(response);
                }
			});

            MessageToast.show("Starting process");
		},
		/* ============================================================ */
		/* Helper Methods for Charts                                    */
		/* ============================================================ */
		/**
		 * Updated the Viz Frame in the view.
		 *
		 * @private
		 * @param {sap.viz.ui5.controls.VizFrame} vizFrame Viz Frame that needs to be updated
		 */
		_updateVizFrame: function(vizFrame) {
			var oVizFrame = this._constants.vizFrame;
			var oVizFramePath = jQuery.sap.getModulePath(this._constants.sampleName, oVizFrame.modulePath);
			var oModel = new JSONModel(oVizFramePath);
			var oDataset = new FlattenedDataset(oVizFrame.dataset);

			vizFrame.setVizProperties(oVizFrame.properties);
			vizFrame.setDataset(oDataset);
			vizFrame.setModel(oModel);
			this._addFeedItems(vizFrame, oVizFrame.feedItems);
			vizFrame.setVizType(oVizFrame.type);
		},
		/**
		 * Updated the Table in the view.
		 *
		 * @private
		 * @param {sap.m.table} table Table that needs to be updated
		 */
		_updateTable: function(table) {
			var oTable = this._constants.table;
			var oTablePath = jQuery.sap.getModulePath(this._constants.sampleName, oTable.modulePath);
			var oTableModel = new JSONModel(oTablePath);
			var aColumns = this._createTableColumns(oTable.columnLabelTexts);

			for (var i = 0; i < aColumns.length; i++) {
				table.addColumn(aColumns[i]);
			}

			var oTableTemplate = new ColumnListItem({
				type: MobileLibrary.ListType.Active,
				cells: this._createLabels(oTable.templateCellLabelTexts)
			});

			table.bindItems(oTable.itemBindingPath, oTableTemplate);
			table.setModel(oTableModel);
		},
		/**
		 * Adds the passed feed items to the passed Viz Frame.
		 *
		 * @private
		 * @param {sap.viz.ui5.controls.VizFrame} vizFrame Viz Frame to add feed items to
		 * @param {Object[]} feedItems Feed items to add
		 */
		_addFeedItems: function(vizFrame, feedItems) {
			for (var i = 0; i < feedItems.length; i++) {
				vizFrame.addFeed(new FeedItem(feedItems[i]));
			}
		},
		/**
		 * Creates table columns with labels as headers.
		 *
		 * @private
		 * @param {String[]} labels Column labels
		 * @returns {sap.m.Column[]} Array of columns
		 */
		_createTableColumns: function(labels) {
			var aLabels = this._createLabels(labels);
			return this._createControls(Column, "header", aLabels);
		},
		/**
		 * Creates label control array with the specified texts.
		 *
		 * @private
		 * @param {String[]} labelTexts text array
		 * @returns {sap.m.Column[]} Array of columns
		 */
		_createLabels: function(labelTexts) {
			return this._createControls(Label, "text", labelTexts);
		},
		/**
		 * Creates an array of controls with the specified control type, property name and value.
		 *
		 * @private
		 * @param {sap.ui.core.Control} Control Control type to create
		 * @param {String} prop Property name
		 * @param {Array} propValues Value of the control's property
		 * @returns {sap.ui.core.Control[]} array of the new controls
		 */
		_createControls: function(Control, prop, propValues) {
			var aControls = [];
			var oProps = {};
			for (var i = 0; i < propValues.length; i++) {
				oProps[prop] = propValues[i];
				aControls.push(new Control(oProps));
			}
			return aControls;
		}

	});
});