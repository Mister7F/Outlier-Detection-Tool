function show_config(config){
	let str = '';
	for(key in config){
		if(key == 'n_outliers' || key == 'run_time')
			continue;
		str += '<b>' + key + '</b>=' + config[key] + '\n<br>';
	}
	
	document.querySelector('.config').innerHTML = str;
}

function search_use_case(search){
	search = search.toLowerCase();
	let rows = document.querySelectorAll('.use_cases tr[hide]');
	for(let i =0; i < rows.length; i++){
		rows[i].removeAttribute('hide');
	}

	rows = document.querySelectorAll('.use_cases tr td:nth-child(1)');
	for(let i =0; i < rows.length; i++){
		if(! rows[i].innerHTML.toLowerCase().includes(search)){
			rows[i].parentNode.setAttribute('hide', '');
		}
	}
}