


// Configuração

var MAPAREAID = "maparea";  // ID da div do mapa
var MAPCENTER = [41.1589, -8.68]; // Latitude e longitude do local central do mapa
var INIT_ZOOMLEVEL = 14; // nível de zoom inicial

var LAYERS = {
	/* BASE: {
		url: 'https://mipweb.cm-porto.pt/arcgis/rest/services/leves/POI/MapServer/0',
		cluster: false,
		where: "classe = 'PRAIAS'",
		type: "point",
		styleFunc: function (lyrobj, valcampo) {
			return {
				url: 'https://mipweb.cm-porto.pt/l/img/praias_28x28.png',
				size: [28, 28],
				anchor: [14, 14],
				popupanchor: [0, -12],
				shadowUrl: 'https://mipweb.cm-porto.pt/l/img/halo.png',
				shadowSize: [36, 36],
				shadowAnchor: [18, 18]
			}
		}
	} */
};

var POPUPCFG = {
	/*BASE: {
		camponome: "nome",
		popupformat: "<p><i><b>{0}</i></b></p>",
		attribformat: "{0}: <b>{1}</b></br>",
		xclatribs: ["usrreg", "classe", "gid"],
		chaveurl: "gid",
		opensametab: true,
		url: {
			1: "http://www.cm-porto.pt/praias/praia-do-castelo-do-queijo",
			2: "http://www.cm-porto.pt/praias/praia-das-pastoras",
			3: "http://www.cm-porto.pt/praias/praia-do-carneiro",
			4: "http://www.cm-porto.pt/praias/praia-do-ourigo",
			5: "http://www.cm-porto.pt/praias/praias-dos-ingleses",
			6: "http://www.cm-porto.pt/praias/praia-de-gondarem-_2",
			7: "http://www.cm-porto.pt/praias/homem-do-leme",
			8: "http://www.cm-porto.pt/praias/praia-da-luz_2"
		}		
	} */
}



