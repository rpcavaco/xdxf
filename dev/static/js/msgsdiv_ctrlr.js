//** Config ** inclui config
var MessagesController = {
	
	// Constantes
	elemid: "msgsdiv",
	messageTimeout: 7000,
	shortMessageTimeout: 4000,
	
	messageText: "",
	isvisible: false,
	timer: null,

	init: function(p_failfunc) {

		const msgsdiv = document.getElementById(this.elemid);
		if (msgsdiv == null) {
			p_failfunc();
			throw new Error("MessagesController: não existe o elemento HTML raíz da caixa de mensagens: "+this.elemid);
		}

		(function(p_this, p_msgdiv) {
			p_msgdiv.addEventListener('click', function(ev) {
				p_this.hideMessage("true");
			});
		})(this, msgsdiv);

	},

	setMessage: function(p_msg_txt, p_is_timed, p_is_warning) {

		this.messageText = p_msg_txt;
		var iconimg=null, msgsdiv = document.getElementById(this.elemid);
		if (this.timer != null) {
			clearTimeout(this.timer);
			this.timer = null;
		}
		if (msgsdiv!=null) {

			while (msgsdiv.firstChild) {
				msgsdiv.removeChild(msgsdiv.firstChild);
			}			
			iconimg = document.createElement("img");
			if (p_is_warning) {
				iconimg.src = "media/warning-5-32.png";
			} else {
				iconimg.src = "media/info-3-32.png";
			}

			msgsdiv.appendChild(iconimg);
			
			var p = document.createElement("p");
			p.insertAdjacentHTML('afterBegin', this.messageText);
			msgsdiv.appendChild(p);
			
			msgsdiv.style.display = '';
			msgsdiv.style.opacity = 1;
			this.isvisible = true;
		}

		let tmo;
		if (p_is_timed) {			
			if (p_is_warning) {
				tmo = this.shortMessageTimeout;
			} else {
				tmo = this.messageTimeout;
			}
			this.timer = setTimeout(function() { MessagesController.hideMessage(true); }, tmo);
		}
	},
	
	hideMessage: function(do_fadeout) {
		if (!this.isvisible) {
			return;
		}
		this.timer = null;
		var msgsdiv = document.getElementById(this.elemid);
		this.isvisible = false;
		if (do_fadeout) 
		{
			fadeout(msgsdiv);
		} 
		else 
		{
			if (msgsdiv!=null) {
				msgsdiv.style.display = 'none';
			}
		}
	}  	
}