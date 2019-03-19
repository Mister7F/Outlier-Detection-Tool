function show_page(page_number, page_size){
	
	if(page_number >= document.querySelector('#n_pages').innerHTML)
		page_number = document.querySelector('#n_pages').innerHTML - 1;
	if(page_number < 0)
		page_number = 0;

	let hide_std_null = document.querySelector('#hide_null_std').checked;
	let hide_no_out = document.querySelector('#hide_no_out').checked;
	let search_filter = document.querySelector('#search').value;
	
	document.querySelector('#page_number').value = page_number;
	document.querySelector('#page_size').value = page_size;
	
	let use_case = document.querySelector('#use_case').getAttribute('value');
	
	let url = '/page/' + use_case + '/' + page_size + '/' + page_number + '/' + (hide_no_out | 0) + '/' + (hide_std_null | 0);
	if(search_filter.length)
		url +=  '/' + search_filter;
	
	fetch(url)
	.then(function(response) {
		return response.text();
	})
	.then(function(response) {

		let data = JSON.parse(response);
		document.querySelector('#n_pages').innerHTML = data['n_pages'];
		data = data['plots'];
		let plots = document.querySelector('.plots');
		plots.innerHTML = '';
		for(let key in data){
			plots.innerHTML += '<img src="/files/' + data[key]['img'] + '" outlier=' + data[key]['n_outliers'] + ' null_std=' + data[key]['one_col'] + '>'
		}
	});
}

window.onload = function(){
	let page_size = document.querySelector('#page_size').getAttribute('value');
	let page_number = document.querySelector('#page_number').getAttribute('value');
	show_page(page_number, page_size);
}



document.addEventListener('DOMContentLoaded', function() {
	var elems = document.querySelectorAll('.tooltipped');
	var instances = M.Tooltip.init(elems, {'position': 'bottom', 'enterDelay': 0});
});