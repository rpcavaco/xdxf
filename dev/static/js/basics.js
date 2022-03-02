
function getWinsize(){
    return {
		width: window.innerWidth || document.body.clientWidth,
		height: window.innerHeight || document.body.clientHeight,
	};
}

function uploadFiles(p_url, p_files, p_onload_func) {
    const formData = new FormData();
  
    for (let i = 0, file; file = p_files[i]; ++i) {
      formData.append("fileobj"+i, file);
    }
  
    const xhr = new XMLHttpRequest();
    xhr.open('POST', p_url, true);
    xhr.onload = p_onload_func;
  
    xhr.send(formData);  // multipart/form-data
}

function getData(p_path, p_resptype, p_onloadfunc, opt_onerrorfunc) {
    
    const xhr = new XMLHttpRequest();
    xhr.open('GET', p_path, true);
    xhr.responseType = p_resptype; // "text", "json", "arraybuffer", "blob", or "document"

    xhr.onload = function(e) {
        if (this.status == 200) {
            p_onloadfunc(this, e);
        } else if (opt_onerrorfunc) {
            opt_onerrorfunc(this, e);
        }
    };
    
    xhr.send();
}

function fadeout(element, heartbeat, finalcallback) {
    var op = 1;  // initial opacity
    var timer = setInterval(function () {
        if (op <= 0.1){
            clearInterval(timer);
            element.style.display = 'none';
            if (finalcallback) {
                finalcallback();
            }
        }
        element.style.opacity = op;
        element.style.filter = 'alpha(opacity=' + op * 100 + ")";
        op -= op * 0.1;
    }, heartbeat);
    return timer;
}

function fadein(element) {
    var op = 0.1;  // initial opacity
    element.style.display = 'block';
    var timer = setInterval(function () {
        if (op >= 1){
            clearInterval(timer);
        }
        element.style.opacity = op;
        element.style.filter = 'alpha(opacity=' + op * 100 + ")";
        op += op * 0.1;
    }, 10);
}

function upToAncestorTag(p_startel, p_tag, p_ctrlcnt) {
    
    let ret=null, cnt=0, tmpel = p_startel;

    while (tmpel.tagName.toLowerCase() != p_tag.toLowerCase() && cnt < p_ctrlcnt) {
        cnt++;
        tmpel = tmpel.parentNode;
    }

    if (tmpel.tagName.toLowerCase() == p_tag.toLowerCase()) {
        ret = tmpel;
    }

    return ret;
}

function filltable(p_tableid, p_coltitles, p_getdata_response, op_fields_list, op_escolha, op_group_rows, op_selrowfunc) {

    const wdg = document.getElementById(p_tableid); // widget: <table> element
    if ( wdg == null ) {
        throw new Error("widget '" + p_tableid + "' não existe"); 
    }
    if ( wdg.tagName.toLowerCase() != "table" ) {
        throw new Error("'" + p_tableid + "' não é <table>"); 
    }

    let rows = [], vrow, vrow_prev, drow, cell, chk;

    class Cell {
        constructor(value) {
            this.value = value;
            this.empty = false;
            this.rowspan = 1;
        }
        addRowspan(addval) {
            if (this.empty) {
                throw new Error("Tentativa de 'Cell.addRowspan' em celula esvaziada, tem valor:"+this.value);
            }
            this.rowspan += addval;
        }
        setEmpty() {
            this.rowspan = 1;
            this.empty = true;
        }
        toString() {
            return "val:" + this.value + ", empty:" + this.empty + ", rowspan:" + this.rowspan;
        }  
    }

    function cellVal(p_i, p_thi) {
        let ret;
        if (op_fields_list) {
            ret = p_getdata_response[p_i][op_fields_list[p_thi]];
        } else {
            ret = p_getdata_response[p_i][p_thi];
        }   
        return ret;
    } 

    for (let i=0; i<p_getdata_response.length; i++) {
        rows.push([]);
        vrow = rows[rows.length-1];
        for (let thi=0; thi<p_coltitles.length; thi++) {
            vrow.push(new Cell(cellVal(i, thi)));
        }
    }

    if (op_group_rows != null && op_group_rows.length > 0) {
        for (let j=0; j<op_group_rows.length; j++) {
            for (let k=rows.length-1; k>0; k--) {
                vrow_prev = rows[k-1];
                vrow = rows[k];
                if (vrow[j].value == vrow_prev[j].value) {
                    vrow_prev[j].addRowspan(vrow[j].rowspan);
                    vrow[j].setEmpty();
                }
            }
        }
    }

    while (wdg.lastChild) {
        wdg.removeChild(wdg.lastChild);
    }  
	const thead = document.createElement("thead");   
	wdg.appendChild(thead);               
	const tbody = document.createElement("tbody");   
	wdg.appendChild(tbody);               

    drow = document.createElement("tr");
    if (op_escolha) {
        cell = document.createElement("th");
        cell.innerText = "Sel";
        drow.appendChild(cell);
    }

    for (let thi=0; thi<p_coltitles.length; thi++) {
        cell = document.createElement("th");
        cell.innerText = p_coltitles[thi];
        drow.appendChild(cell);
    }
    thead.appendChild(drow);

    if (rows.length > 0) {

        for (let ri=0; ri<rows.length; ri++) {
            
            drow = document.createElement("tr");
            vrow = rows[ri];

			if (op_selrowfunc) {
				(function (p_selrowfunc, p_wdg, p_rowid) {
					p_wdg.addEventListener('click', function (ev) {
						p_selrowfunc(p_rowid, p_wdg);
						ev.stopPropagation();
					});
				})(op_selrowfunc, drow, ri);
			}

            if (op_escolha) {
                cell = document.createElement("td");
                chk = document.createElement("input");
                chk.setAttribute("type", "checkbox");

                (function (p_check) {
                    p_check.addEventListener('click', function (ev) {
                        let lcell, lchk, escolhaval = null;
                        const tableEl = upToAncestorTag(ev.target, "table", 4);
                        if (tableEl) {
                            for (let ri=0; ri<tableEl.rows.length; ri++) {
                                lcell = tableEl.rows[ri].cells[0];
                                if (lcell) {
                                    lchk = lcell.firstChild;
                                    if (lchk && lchk != ev.target) {
                                        lchk.checked = false;
                                    } else if (op_escolha['val_col'] !== undefined && lchk.checked) {
                                        if (op_escolha.val_col < 1) {
                                            escolhaval = ri-1;
                                        } else {
                                            escolhaval = tableEl.rows[ri].cells[op_escolha.val_col].innerText;
                                        }
                                    }
                                }
                                
                            }
                        }
                        if (op_escolha['action'] !== undefined) {
                            op_escolha['action'](ev, escolhaval);
                        }
                    });
                })(chk);

                cell.appendChild(chk);
                drow.appendChild(cell);
            }

            for (let ci=0; ci<vrow.length; ci++) {
                if (!vrow[ci].empty) {
                    cell = document.createElement("td");
                    if (vrow[ci].rowspan > 1) {
                        cell.setAttribute("rowspan", vrow[ci].rowspan);
                    }
                    cell.innerText = vrow[ci].value;
                    drow.appendChild(cell);
                }
            }

            tbody.appendChild(drow);

        }

    } else {

        cell = document.createElement("td");
        cell.setAttribute("colspan", p_coltitles.length);
        cell.innerText = "(sem dados)";
        drow = document.createElement("tr");
        drow.appendChild(cell);
        wdg.appendChild(drow);

    }

	return wdg;
}

const uuidv4 = () => {
    const hex = [...Array(256).keys()]
      .map(index => (index).toString(16).padStart(2, '0'));
  
    const r = crypto.getRandomValues(new Uint8Array(16));
  
    r[6] = (r[6] & 0x0f) | 0x40;
    r[8] = (r[8] & 0x3f) | 0x80;
    
    return [...r.entries()]
      .map(([index, int]) => [4, 6, 8, 10].includes(index) ? `-${hex[int]}` : hex[int])
      .join('');
  };

function removeOptions(selectElement) {
	let i, L = selectElement.options.length - 1;
	for(i = L; i >= 0; i--) {
	   selectElement.remove(i);
	}
}

function widgetsToDict(p_widgetidlist, p_errorfunc, out_dict) {
	let falha = false;
	for (let x, id, i=0; i<p_widgetidlist.length; i++) {
		id = p_widgetidlist[i];
		x = document.getElementById(id);
		if (x == null) {
			p_errorfunc(id);
			falha = true;
			break;
		} else {
			out_dict[id] = x;
		}
	}
	return falha;
}

function getSelOption(p_wdg) {
	return p_wdg.options[p_wdg.selectedIndex].value;
}

function parseBool(val) { return val === true || val === "true" }