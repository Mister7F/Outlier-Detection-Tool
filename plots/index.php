<!DOCTYPE html>
<html>
<head>
	<title>Use cases</title>
	<link rel='stylesheet' type='text/css' href='static/index.css'>
	<script src='static/index.js'></script>
	<link rel='stylesheet' type='text/css' href='//fonts.googleapis.com/css?family=Open+Sans'/>
</head>
<body>

<?php
function endsWith($string, $endString){ 
    $len = strlen($endString); 
    if ($len == 0) { 
        return true; 
    } 
    return (substr($string, -$len) === $endString); 
}

$blacklist = ['.', '..', 'static', 'index.php'];

if(isset($_GET['use_case'])){
	$use_case = $_GET['use_case'];
	if(in_array($use_case, scandir('.')) && ! in_array($use_case, $blacklist)){
		?>
		<div class='plots'>
			<div>
				<div onclick='document.location= "/";' style='cursor: pointer'>Go back</div>
				<input type='checkbox' id='hide_no_out' onchange='update_plots()'/>
				<label for='hide_no_out'>Hide if no outlier</label>
				<br>
				<input type='checkbox' id='hide_zero_std' onchange='update_plots()'/>
				<label for='hide_zero_std'>Hide if std is null</label>
			</div>
			<div>
		<?php
			foreach(scandir($use_case) as $file){
				if(endsWith($file, '.svg')){
					echo '<img src="' . $use_case . '/' . $file . '"/>';
				}
			}
		?>
			</div>
		</div>
	<?php
	}
	else{
		echo 'Wrong use-case';
	}	
}
else{
	?>
	<div class='use_cases'>
		<?php
			foreach(scandir('./') as $dir){
				if(in_array($dir, $blacklist))
					continue;

				echo '<div onclick="show(\'' . $dir . '\')">' . $dir . '</div>';
			}
		?>
	</div>
	<?php
}
?>

</body>
</html>


