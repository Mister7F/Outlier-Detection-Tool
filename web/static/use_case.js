function update_img(){
	let hide_std_null = document.querySelector('#hide_null_std').checked;
	let hide_no_out = document.querySelector('#hide_no_out').checked;

	console.log(hide_no_out);

	for(let img of document.querySelectorAll('.plots img[hide]')){
		img.removeAttribute('hide');
	}
	if(hide_no_out){
		for(let img of document.querySelectorAll('.plots img[outlier="False"]')){
			img.setAttribute('hide', '');
		}
	}
	if(hide_std_null){
		for(let img of document.querySelectorAll('.plots img[null_std="True"]')){
			img.setAttribute('hide', '');
		}
	}
}