




// ------------------------------------------------------------------------
// Parâmetros comuns a todos os mapas
// ------------------------------------------------------------------------
// Constantes - CUIDADO NA ALTERAÇÃO DE CONTEÚDO DESTE BLOCO --------------

var MAXZOOMLEVEL = 19;
var MAPCTRL = null;

var TILED_BASEMAP_LAYERS = {
	ORTOIMG: {
		label: "Ortoimagem",
		url: 'https://mipweb.cm-porto.pt/agol/{z}/{x}/{y}.jpg',
		esri: false,
		minZoom: 12,
		maxZoom: 17,
		attribution: "<a href='https://www.arcgis.com/home/item.html?id=64f2ff721fe744f3ad47497cf149b863'>ESRI</a>"		
	},
	TEMASBASE: {
		label: "Temas base",
		url: 'https://mipweb.cm-porto.pt/arcgis/rest/services/Cache/CACHE_INFO_BASE_XPL4/MapServer',
		esri: true,
		minZoom: 14,
		maxZoom: MAXZOOMLEVEL,
		attribution: "C.M.Porto"		
	}
}


var INSTANCED_LAYERS = {};
var MERGE_BASEMAP_LAYERS = true;

// --------- Final parametros ---------------------------------------------


// ------------------------------------------------------------------------
// Pre-requesitos
// ------------------------------------------------------------------------

function finishEvent(e){
    if(e.stopPropagation) {
		e.stopPropagation();
	} else {
		e.cancelBubble=true;
	}
    if(e.preventDefault) {
		e.preventDefault();
	}
    return false;
}

 if (!String.format) {
	  String.format = function(format) {
		if (typeof format == "undefined" || format == null) {
			throw new Error("String format using null format");
		}
	    var args = Array.prototype.slice.call(arguments, 1);
	    return format.replace(/{(\d+)}/g, function(match, number) { 
	      return typeof args[number] != 'undefined'
	        ? args[number] 
	        : match
	      ;
	    });
	  };
}

function ajaxSender(url, reqListener, postdata, opt_req, opt_cors_compatmode, opt_rec_blob)
{
	var oReq;
	
	if (opt_req != null) {
		oReq = opt_req;
	} else {
		if (opt_cors_compatmode && typeof XDomainRequest != 'undefined') {
			oReq = new XDomainRequest();
		} else {
			oReq = new XMLHttpRequest();
		}
	}
	
	if (opt_cors_compatmode && typeof XDomainRequest != 'undefined') {	
		oReq.onload = reqListener;
	} else {
		oReq.onreadystatechange = reqListener;
	}
	
	var meth, finalurl;
	
	if (postdata != null)
	{
		meth = "POST";
		finalurl = url;
	}
	else
	{
		meth = "GET";
		// para prevenir o caching dos pedidos 
		finalurl = url + ((/\?/).test(url) ? "&_ts=" : "?_ts=") + (new Date()).getTime();
	}

	if (opt_cors_compatmode && typeof XDomainRequest != 'undefined') {
		oReq.open(meth, finalurl);
	} else {
		oReq.open(meth, finalurl, true);
	}

	if (postdata && oReq.setRequestHeader !== undefined && oReq.setRequestHeader != null)
	{
		oReq.setRequestHeader('Content-type','application/json');  
	}
	
	if (opt_rec_blob) {
		oReq.responseType = 'blob';
	}
	
	oReq.send(postdata);
	
	return oReq;

}

var isIE = false || !!document.documentMode; 

function isElement( o)
{
	if (!isIE)
	{ return o instanceof Element }
	else
	{ return o && o.nodeType == 1 && o.tagName != undefined }
}

function getClass(elem) {
	var classname = '';
	if (isElement(elem)) {
		if (typeof elem.getAttribute != 'undefined') {
			classname = elem.getAttribute('class');
		} else {
			classname = elem.className;
		}	
	}	
	
	return classname;
}

function setClass(p_node, p_class_str) {
	
	var final_classes, v_classes_str = getClass(p_node);
	if (v_classes_str == null || v_classes_str.length < 1) {
		v_classes = [];
	} else {
		v_classes = v_classes_str.split(/[ ]+/);
	}
	
	if (v_classes.indexOf(p_class_str) >= 0) {
		return;
	}
	
	v_classes.push(p_class_str);
	
	final_classes = v_classes.join(' ');

	if (final_classes.length > 0) {	
		p_node.className = final_classes;
	} else {
		p_node.className = "";
	}
}

function unsetClass(p_node, p_class_str) {
	
	var v_classes_str = getClass(p_node);
	if (v_classes_str == null || v_classes_str.length < 1) {
		return;
	}
	var final_classes, v_classes = v_classes_str.split(/[ ]+/);
	
	if (v_classes.indexOf(p_class_str) >= 0) {
		v_classes.splice(v_classes.indexOf(p_class_str), 1);
	}
	
	final_classes = v_classes.join(' ');

	if (final_classes.length > 0) {	
		p_node.className = final_classes;
	} else {
		p_node.className = "";
	}
}


// ------------------------------------------------------------------------
// Funcionalidades de mapa
// ------------------------------------------------------------------------

function getIconCfg(p_layerkey, p_cfgico) {
	
	var cfgicoobj = {
		className: "lyr_" + p_layerkey
	}, requiredcount = 0;
	
	for (var kcfgico in p_cfgico) 
	{
		if (!p_cfgico.hasOwnProperty(kcfgico)) {
			continue;
		}
		switch (kcfgico) {
			case "url":
				cfgicoobj.iconUrl = p_cfgico[kcfgico];
				requiredcount++;
				break;
			case "size":
				cfgicoobj.iconSize = p_cfgico[kcfgico];
				requiredcount++;
				break;
			case "anchor":
				cfgicoobj.iconAnchor = p_cfgico[kcfgico];
				break;
			/*case "classname":
				cfgicoobj.className = p_cfgico[kcfgico];
				break; */
			default:
				cfgicoobj[kcfgico] = p_cfgico[kcfgico];
				
		}
	}	
	
	if (requiredcount < 2) {
		if (console) {
			console.trace("Icon sem os atributos mínimos requeridos.");
			console.warn(p_cfgico);
		}
		return null;
	} else {
		return cfgicoobj;
	}

}

function buildpopup(e, p_tpopobj, p_layerkey) {

	var d, content="", attr, attrlbl, attrval, attrs, attrcontent='', tit='';
	var cv=null, props = e.sourceTarget.feature.properties;
	var has_date, attrnome=null;	
	
	/*console.log(p_layerkey);
	console.log(p_tpopobj);
	console.log(props);
	console.log("............."); */
	
	if (props[p_tpopobj.camponome] !== undefined && props[p_tpopobj.camponome] != null) {		
		cv = p_tpopobj['codedvals'][p_tpopobj.camponome];
		if (cv!=null && cv[props[p_tpopobj.camponome]]!=null) {
			tit = cv[props[p_tpopobj.camponome]];
		} else {
			tit = props[p_tpopobj.camponome];
		}
		attrnome = p_tpopobj.camponome;
	} else {
		tit = '(sem designação)';
	}

	cv = null;
	
	if (p_tpopobj.popupformat !== undefined && p_tpopobj.popupformat != null) {

		if (p_tpopobj.orderedatribs !== undefined && p_tpopobj.orderedatribs != null && p_tpopobj.orderedatribs.length) {
			
			if (p_tpopobj.attribformat === undefined) {
				throw new Error("");
			}
			
			if (props.jsonattrs !== undefined && props.jsonattrs != null && props.jsonattrs.length > 0) {
				attrs = JSON.parse(props.jsonattrs);
			} else {
				attrs = props;
			}
			for (var oi=0; oi<p_tpopobj.orderedatribs.length; oi++) {
				attr = p_tpopobj.orderedatribs[oi];
				
				if (attr == attrnome) {
					continue;
				}
				
				attrlbl = p_tpopobj.atriblabels[attr];
				attrval = attrs[attr];
				
				cv = p_tpopobj['codedvals'][attr];
				has_date = (p_tpopobj.dateflds != undefined);
				
				if (cv) {
					attrval = cv[attrval];
				} else if ( has_date && attrval != null ) {
					if (p_tpopobj.dateflds.indexOf(attr) >= 0) {
						d = new Date(0);
						if (attrval.toString().length > 10) {
							d.setUTCSeconds(attrval / 1000);
						} else {
							d.setUTCSeconds(attrval);
						}
						attrval = d.toLocaleDateString();
					}
				}
				
				if (attrval == null || attrval == "null" || attrval == "undefined") {
					attrval = "";
				}
				if (attrval!=null && String.format("{0}", attrval).length > 0) {
					attrcontent +=  String.format(p_tpopobj.attribformat, attrlbl, attrval);
				}
			}
			content = String.format(p_tpopobj.popupformat, tit) + attrcontent;			
		}	
	} else {
		content = tit;
	}

	return content;
}

function clickfunc(e, p_map, p_tpopobj, p_layerkey) {

	var content, urls, url=null, keyv, props = e.sourceTarget.feature.properties;
	var winopened = false;

	if (typeof MODEPOPUP == "undefined" || MODEPOPUP == "MOVE") {
		
		//console.log(props);
		if (props[p_tpopobj.chaveurl] !== undefined && props[p_tpopobj.chaveurl] != null) {
			keyv = props[p_tpopobj.chaveurl];
			if (p_tpopobj.url !== undefined && p_tpopobj.url != null) {
				urls = p_tpopobj.url;
				if (urls[keyv] !== undefined && urls[keyv] != null) {
					url = urls[keyv];
				}
			}
		}

		if (url) {
			window.open(url, "_self");
			winopened = true;
		}
	}

	if (!winopened) {

		content = buildpopup(e, p_tpopobj, p_layerkey);
		if (content.length) {
			L.popup()
				.setLatLng(e.latlng) 
				.setContent(content)
				.openOn(p_map);
		}
		
	}
}

function moverfunc(e, p_map, p_tpopobj, p_layerkey) {

	var content = buildpopup(e, p_tpopobj, p_layerkey);	
	if (content.length) {
		L.popup()
			.setLatLng(e.latlng) 
			.setContent(content)
			.openOn(p_map);
	}
	
}
	
function removeLayer(lyrkey) {
	if (INSTANCED_LAYERS[lyrkey] !== undefined) {
		MAPCTRL.removeLayer(INSTANCED_LAYERS[lyrkey]);
		delete INSTANCED_LAYERS[lyrkey];
	}	
}

function addLayer(lyrkey, p_default) {
	
	// p_default - carregamento apenas se layer nao for opcional
	
	var fetobj, cfgicoobj, ptlfunc, polfunc, isclustered = false, wherecl='';
	
	if (LAYERS[lyrkey] === undefined) {
		return;
	}

	tlobj = LAYERS[lyrkey];
	if (tlobj.opcional !== undefined && tlobj.opcional && p_default) {
		return;
	}
	if (tlobj.url === undefined) {
		throw new Error("LAYERS -- layer mal definida, sem URL:" + lyrkey);
	}
	if (INSTANCED_LAYERS[lyrkey] !== undefined) {
		if (console) {
			console.warn("Layer "+lyrkey+" ja esta adicionada ao mapa");
		}
		return;
	}
	if (tlobj.type === undefined) {
		if (console) {
			console.warn("Layer "+lyrkey+" sem tipo de geometria definido");
		}
		return;		
	}
	if (tlobj.type == 'points' || tlobj.type == 'point') {
		// POINTS

		if (tlobj.cluster !== undefined && tlobj.cluster != null && tlobj.cluster) {
			isclustered = true;
		}
		if (tlobj.where !== undefined && tlobj.where != null) {
			wherecl = tlobj.where;
		}

		if (tlobj.nomecampo === undefined || tlobj.nomecampo == null) {
			
			ptlfunc = (function(p_tlobj) {
				return function (feature, latlng) {
					var cfgicoobj =  getIconCfg(lyrkey, p_tlobj.styleFunc(p_tlobj, feature));
					return 	L.marker(latlng, {
						icon: L.icon(cfgicoobj)
					});
				}
			})(tlobj);
			
		} else {
			
			ptlfunc = (function(p_tlobj) {
				return function (feature, latlng) {
					var cfgicoobj =  getIconCfg(lyrkey, p_tlobj.styleFunc(p_tlobj, feature.properties[p_tlobj.nomecampo]));
					return 	L.marker(latlng, {
						icon: L.icon(cfgicoobj)
					});
				}
			})(tlobj);
		}

		if (ptlfunc == null) {
			throw new Error("mapinit(): layer '"+lyrkey+"' sem pointToLayer function.");
		}
		
		fetobj = {
			url: tlobj.url,
			pointToLayer: ptlfunc
		}
	} else {
		if (tlobj.type != 'polys' && tlobj.type != 'poly' && tlobj.type != 'line') {
			throw new Error("LAYERS -- layer mal definida " + lyrkey + ", tipo errado: "+tlobj.type);
		}
		
		// polys
		if (tlobj.where !== undefined && tlobj.where != null) {
			wherecl = tlobj.where;
		}
		
		if (tlobj.styleFunc === undefined) {
			throw new Error("mapinit(): layer '"+lyrkey+"' sem 'style' function.");
		}
		
		polfunc = (function(p_tlobj) {
			return function (feature) {
				return p_tlobj.styleFunc(p_tlobj, feature);
			}
		})(tlobj);
		
		fetobj = {
			url: tlobj.url,
			style: polfunc,
			className: "lyr_" + lyrkey
		}
			
		if (tlobj.simplifyFactor!==undefined) {
			fetobj.simplifyFactor = tlobj.simplifyFactor;
		}
		if (tlobj.precision!==undefined) {
			fetobj.precision = tlobj.precision;
		}
		if (tlobj.maxZoom!==undefined) {
			fetobj.maxZoom = tlobj.maxZoom;
		}
		if (tlobj.minZoom!==undefined) {
			fetobj.minZoom = tlobj.minZoom;
		}
	}
	
	if (wherecl) {
		fetobj.where = wherecl;
	}

	var lyr;
	if (isclustered) {
		lyr = L.esri.Cluster.featureLayer(fetobj).addTo(MAPCTRL);
	} else {
		lyr = L.esri.featureLayer(fetobj).addTo(MAPCTRL);
	}; 
	
	INSTANCED_LAYERS[lyrkey] = lyr;
	
	/*
	* Config popup e interacção com utilizador
	*
	* */

	var ppcfg = null;
	if (typeof POPUPCFG != 'undefined') {
		ppcfg = POPUPCFG;
	}
	if (ppcfg != null && ppcfg.hasOwnProperty(lyrkey)) {

		tpopobj = ppcfg[lyrkey];

		if (tpopobj.camponome === undefined) {
			throw new Error("POPUPCFG -- layer '"+tblkey+"' mal definida, sem 'camponome'");
		}
		if (tpopobj.chaveurl !== undefined || tpopobj.chaveurl != null) {
			if (tpopobj.url === undefined || tpopobj.url == null) {
				throw new Error("POPUPCFG -- layer '"+tblkey+"' mal definida, tem 'chaveurl' mas não tem o dicionário de URLs definido");
			}
		} else {
			if (console) {
				console.warn("Verifica-se que o tema '"+p_lyrkey+"' não tem 'chaveurl' definido, não terá navegaçao a partir dos objetos geográficos.");
			}
		}
		
		if (tpopobj.attribformat === undefined) {
			throw new Error(String.format("Layer '{0}' n˜ao tem 'attribformat' definido no objeto de configuraç˜ao POPUPCFG", lyrkey));
		};

		(function(p_lyr, p_map, p_tpopobj) {
			p_lyr.on('click', function(e) {
				clickfunc(e, MAPCTRL, p_tpopobj, lyrkey);
			});	
			p_lyr.on('mouseover', function(e) {
				if (typeof MODEPOPUP == "undefined" || MODEPOPUP == "MOVE") {
					moverfunc(e, MAPCTRL, p_tpopobj, lyrkey);
				}
			});	
			p_lyr.on('touch', function(e) {
				clickfunc(e, MAPCTRL, p_tpopobj, lyrkey);
			});	
		})(lyr, MAPCTRL, tpopobj);

	}

};

function checkMarkerScaleViz() {
	var els, dohide, zoomv;
	for (var lyrkey in LAYERS) {
		
		if (!LAYERS.hasOwnProperty(lyrkey)) {
			continue;
		}
		
		dohide = false;
		zoomv = MAPCTRL.getZoom();
				
		if (LAYERS[lyrkey].minZoom !== undefined && LAYERS[lyrkey].minZoom > zoomv) {
			dohide = true;
		} else if (LAYERS[lyrkey].maxZoom !== undefined && LAYERS[lyrkey].maxZoom < zoomv) {
			dohide = true;
		}

		//console.log("lyr:"+lyrkey+", mz:"+MAPCTRL.getZoom()+" min:"+LAYERS[lyrkey].minZoom+" max:"+LAYERS[lyrkey].maxZoom+" dohide:"+dohide);
		
		els = document.getElementsByClassName("lyr_" + lyrkey);
		for (var i=0; i<els.length; i++) {
			if (dohide) {
				setClass(els[i], "vhidden");
			} else {
				unsetClass(els[i], "vhidden");
			}
		}
	};
}
	
function mapinit(p_clear) {

	for (var lyrkey in LAYERS) {
		if (LAYERS.hasOwnProperty(lyrkey)) {
			if (POPUPCFG[lyrkey] === undefined) {
				console.warn(String.format("Layer '{0}' em falta na POPUPCFG", lyrkey));
			}
		}		
	}
	
	for (var lyrkey in POPUPCFG) {
		if (POPUPCFG.hasOwnProperty(lyrkey)) {
			if (LAYERS[lyrkey] === undefined) {
				console.warn(String.format("Layer '{0}' existe em POPUPCFG mas falta em LAYERS", lyrkey));
			}
		}		
	}

	var k, lk, lyrobj, mlyrobj, isesri=false;
	let basemapControl, prevBounds = null;
	
	// Criar classe css vhidden, da qual depende a possibilidade de ligar e desligar a 
	// visualização dos markers duma layer
	var style = document.createElement('style');
	style.type = 'text/css';
	style.innerHTML = '.vhidden { visibility: hidden; }';
	document.getElementsByTagName('head')[0].appendChild(style);
	
	if (p_clear && MAPCTRL !== null) {
		prevBounds = MAPCTRL.getBounds();
		MAPCTRL.remove();
		INSTANCED_LAYERS = {};
		MAPCTRL = null;
		document.getElementById(MAPAREAID).innerHTML = "";
	}

	// ------------------------------------------------------------------------
	// Base map layers
	// ------------------------------------------------------------------------
	basemapControl = {};
	
	MAPCTRL = L.map(MAPAREAID).setView(MAPCENTER, INIT_ZOOMLEVEL);
	
	if (prevBounds) {
		MAPCTRL.fitBounds(prevBounds);
	}

	var isfirst = true;
	for (var tblkey in TILED_BASEMAP_LAYERS) {
		
		lyrobj = {};
		if (!TILED_BASEMAP_LAYERS.hasOwnProperty(tblkey)) {
			continue;
		}	
		k = TILED_BASEMAP_LAYERS[tblkey];

		if (k.esri !== undefined && k.esri != null && k.esri) {
			isesri = true;
		} else {
			isesri = false;
		}

		if (k.url === undefined) {
			throw new Error("TILED_BASEMAP_LAYERS -- layer mal definida, sem URL:" + tblkey);
		}

		for (var lkey in k) {
			if (!k.hasOwnProperty(lkey)) {
				continue;
			}
			if (!isesri && lkey == 'url') {
				continue;
			}
			lyrobj[lkey] = k[lkey];	
		}

		if (k.esri !== undefined && k.esri != null && k.esri) {
			mlyrobj = L.esri.tiledMapLayer(lyrobj);
			if (isfirst) {
				mlyrobj.addTo(MAPCTRL);
			}
		} else {
			mlyrobj = L.tileLayer(k.url, lyrobj);
			if (isfirst) {
				mlyrobj.addTo(MAPCTRL);
			}
		}
		
		if (!MERGE_BASEMAP_LAYERS) {
			basemapControl[lyrobj.label] = mlyrobj;
			isfirst = false;
		}
		
	};
	
	if (!MERGE_BASEMAP_LAYERS) {
		L.control.layers( basemapControl ).addTo( MAPCTRL );
	}

	// ------------------------------------------------------------------------
	// Outras layers
	// ------------------------------------------------------------------------
	
	var tlobj, icon, cfgicoobj, ptlfunc, fetobj = {}, wherecl = null, tpopobj;
	for (var lyrkey in LAYERS) {
		
		if (!LAYERS.hasOwnProperty(lyrkey)) {
			continue;
		}
		
		addLayer(lyrkey, true);
	};

	// ------------------------------------------------------------------------
	// Carregar metadados - campos, etiquetas, dominios de valores
	// ------------------------------------------------------------------------
	var url, tpopobj, fname, v_ok;
	var attrs_forget = ['objectid', 'shape', 'st_area(shape)', 'st_length(shape)', 'user', 'utilizador', 'datareg', 'globalid'];
	for (var lyrkey in LAYERS) {
		
		if (!LAYERS.hasOwnProperty(lyrkey)) {
			continue;
		}
		
		atribspreconfiged = false;
		
		url = LAYERS[lyrkey].url + "?f=json";
		tpopobj = POPUPCFG[lyrkey];
		if (tpopobj) {
			
			if (tpopobj.orderedatribs !== undefined && tpopobj.orderedatribs.length > 0) {
				atribspreconfiged = true;
			} else {
				tpopobj['orderedatribs'] = [];
				tpopobj['atriblabels'] = {};
			}
			
			tpopobj['codedvals'] = {};

			ajaxSender(url, 
				(function(p_lyrkey) {
					return function() {	
						var cv, respobj = {};	
						var loc_tpopobj = POPUPCFG[p_lyrkey];				
						if (this.readyState === this.DONE)
						{
							if (this.status == 200)
							{
								qryres = this.responseText;
								if (qryres.length > 5) {
									respobj = JSON.parse(qryres);
									if (respobj.fields) {
										for (var i=0; i<respobj.fields.length; i++) {
											v_ok = true;
											for (var j=0; j<attrs_forget.length; j++) {
												if (respobj.fields[i].name.indexOf(attrs_forget[j]) >= 0) {
													v_ok = false;
													break;
												}
											}
											if (v_ok && loc_tpopobj.xclatribs !== undefined) {
												if (loc_tpopobj.xclatribs.indexOf(respobj.fields[i].name) >= 0) {
													v_ok = false;
												}												
											}
											//console.log(p_lyrkey+" ok:"+v_ok+" fdl:"+respobj.fields[i].name);
											if (v_ok) {
												fname = respobj.fields[i].name;
												//console.log(" --- "+respobj.fields[i].name+" dom undef:"+(respobj.fields[i].domain === undefined));
												if (loc_tpopobj['orderedatribs'].indexOf(fname) < 0) {
													loc_tpopobj['orderedatribs'].push(fname);
													loc_tpopobj['atriblabels'][fname] = respobj.fields[i].alias.replace('_', ' ');
													if (respobj.fields[i].domain !== undefined && respobj.fields[i].domain != null) {
														loc_tpopobj['codedvals'][fname] = {};
														for (var j=0; j<respobj.fields[i].domain.codedValues.length; j++) {
															cv = respobj.fields[i].domain.codedValues[j];
															loc_tpopobj['codedvals'][fname][cv.code] = cv.name;
														}
													}
												}
											}
										}
									}
								}
								
							}
						}
					}
				})(lyrkey),
				null, // postdata
				null, // opt_req 
				true  // opt_cors_compatmode para IE
			);
		
		}					

	};


	// ------------------------------------------------------------------------
	// Base map layers
	// ------------------------------------------------------------------------

	MAPCTRL.on('zoomend moveend', checkMarkerScaleViz);	
	
	checkMarkerScaleViz();
	
}