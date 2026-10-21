"""Execute every notebook code cell in a clean local IPython process.

Use when the host blocks Jupyter's kernel sockets. This runs actual cells, fails
on the first error, and records captured stdout, rich displays and native plots.
No results are fabricated or copied from an earlier notebook.
"""
import argparse
import base64
import io
import os
from pathlib import Path
import time
import traceback
import nbformat
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from IPython.display import display, Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook')
    args = parser.parse_args()
    path = Path(args.notebook).resolve()
    os.chdir(path.parent.parent)
    notebook = nbformat.read(path, as_version=4)
    prefix, tail = notebook.cells[0].source.split('## tl;dr', 1)
    _, methods = tail.split('## Context & Methods', 1)
    notebook.cells[0].source = prefix + '## tl;dr\n\nExecution in progress; no current-run conclusion yet.\n\n## Context & Methods' + methods
    notebook.metadata.pop('execution_engine', None)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None
    nbformat.write(notebook, path)
    shell = InteractiveShell.instance()
    shell.user_ns['__name__'] = '__main__'
    figure_dir = Path('outputs/figures')
    figure_dir.mkdir(parents=True, exist_ok=True)
    for previous in figure_dir.glob('figure_*.png'):
        previous.unlink()
    figure_count = 0

    def show(*_args, **_kwargs):
        nonlocal figure_count
        for number in list(plt.get_fignums()):
            figure_count += 1
            fig = plt.figure(number)
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            (figure_dir/f'figure_{figure_count:02d}.png').write_bytes(buffer.getvalue())
            display(Image(data=buffer.getvalue()))
            plt.close(fig)
    plt.show = show
    count = 0
    for i, cell in enumerate(notebook.cells):
        if cell.cell_type != 'code':
            continue
        count += 1
        cell.outputs = []
        cell.execution_count = count
        started = time.monotonic()
        print(f'Executing cell {i} (code {count})', flush=True)
        with capture_output(stdout=True, stderr=True, display=True) as captured:
            result = shell.run_cell(cell.source, store_history=False)
        if captured.stdout:
            cell.outputs.append(nbformat.v4.new_output('stream', name='stdout', text=captured.stdout))
            print(captured.stdout[:1100], flush=True)
        if captured.stderr:
            cell.outputs.append(nbformat.v4.new_output('stream', name='stderr', text=captured.stderr))
            print(captured.stderr[:500], flush=True)
        for output in captured.outputs:
            data = {k: base64.b64encode(v).decode() if isinstance(v, bytes) else v
                    for k, v in output.data.items()}
            cell.outputs.append(nbformat.v4.new_output('display_data', data=data,
                                                       metadata=output.metadata))
        cell.metadata['execution_seconds'] = round(time.monotonic()-started, 3)
        error = result.error_before_exec or result.error_in_exec
        if error:
            cell.outputs.append(nbformat.v4.new_output('error', ename=type(error).__name__,
                evalue=str(error), traceback=traceback.format_exception(error)))
            nbformat.write(notebook, path)
            raise RuntimeError(f'Notebook cell {i} failed: {error}') from error
        nbformat.write(notebook, path)
    notebook.metadata['execution_engine'] = {
        'name': 'IPython in-process, fresh Python process; matplotlib Agg capture',
        'reason': 'Host blocks Jupyter TCP kernel sockets',
        'executed_code_cells': count, 'figures': figure_count,
        'completed_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
    summary_path = Path('outputs/RESULTS.md')
    prefix, tail = notebook.cells[0].source.split('## tl;dr', 1)
    _, methods = tail.split('## Context & Methods', 1)
    current_summary = summary_path.read_text().split('\n', 1)[1].strip()
    notebook.cells[0].source = prefix + '## tl;dr\n\n' + current_summary + '\n\n## Context & Methods' + methods
    notebook.metadata['project_revision']['status'] = 'completed real-data retrospective academic study'
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f'COMPLETE: {count} code cells; {figure_count} figures', flush=True)


if __name__ == '__main__':
    main()
