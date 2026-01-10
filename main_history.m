currentFile = mfilename('fullpath');
currentDir = fileparts(currentFile);

try
	pyScript = fullfile(currentDir, 'qlib_code', 'export_test_scores_per_day.py');
	
    path_config = fullfile(currentDir, 'config', 'paths.yaml');

    path = ReadYaml(path_config);
	pythonExe = path.python_exe;

	cmd = sprintf('"%s" -u "%s"', pythonExe, pyScript);
	[status, cmdout] = system(cmd, '-echo');
    if status ~= 0
        warning('Running python script failed (status=%d). Output:\n%s', status, cmdout);
    end
	

catch ME
	% Use identifier-aware warning format to satisfy MATLAB diagnostics
	if isprop(ME, 'identifier') && ~isempty(ME.identifier)
		id = ME.identifier;
	else
		id = 'run_optimizer:pythonImportFail';
	end
	warning(id, 'Failed to launch Python importer: %s', ME.message);
end
addpath(fullfile(currentDir, 'Optimizer_matlab'));	
run_optimizer("history");
