function show(usecase){
	document.location = 'index.php?use_case=' + usecase;
} 

function update_plots(){
	let hide_if_no_out = document.getElementById('hide_no_out').checked;
	let hide_zero_std = document.getElementById('hide_zero_std').checked;
	
	for(let img of document.querySelectorAll('.plots img')){
		src = img.src.split('/');
		src = src[src.length - 1];

		if(hide_if_no_out && ! img.src.match(/\/\*/g)){
			img.setAttribute('hide', '');
		}
		else if(hide_zero_std){
			let std = img.src.split('_');
			std = std[std.length - 2];
			std = parseFloat(std);
			console.log(std);
			if(std < 0.000001)
				img.setAttribute('hide', '');
		}
		else{
			img.removeAttribute('hide');
		}
		console.log(img.src);
	}
}