#!/usr/bin/env python

from argparse import ArgumentParser
from glob import glob
from os import path
from subprocess import run
from tempfile import mkdtemp, NamedTemporaryFile


def clone_repository(repo, branch, target_path):
    run(
        ['git', 'clone', repo, '--depth', '1', '--branch', branch, target_path],
        check=True
    )


def render_helm_chart(chart_path, namespace, release_name, rendered_path):
    # Even if there is no Helm chart at the specified chart path, do not raise an error.
    # This accommodates cases where the entire chart is removed, or a new chart is added.
    # In such cases, the rendered file will simply be empty.
    if path.isdir(chart_path):
        run(
            ['helm', 'dependency', 'update', chart_path],
            check=True
        )

    with(open(rendered_path, 'w')) as rendered_file:
        run(
            ['helm', 'template', '--namespace', namespace, release_name, chart_path],
            stdout=rendered_file,
            check=True
        )


def changed_charts(source_path, target_path, subpath):
    changed_charts = []

    # Convert to set for deduplication
    all_charts = set(
        glob(f"*", root_dir=f"{source_path}/{subpath}")
        + glob(f"*", root_dir=f"{target_path}/{subpath}")
    )

    for chart in all_charts:
        source_chart_path = path.join(source_path, subpath, chart)
        target_chart_path = path.join(target_path, subpath, chart)

        if run(['diff', source_chart_path, target_chart_path], capture_output=True).returncode != 0:
            changed_charts.append(chart)

    return changed_charts


def main():
    parser = ArgumentParser(
        description='Compare Helm charts in a directory between two Git revisions.')
    parser.add_argument('--repository', required=True,
                        help='Repository to clone')
    parser.add_argument('--source', required=True,
                        help='Source branch (e.g. pull request branch)')
    parser.add_argument('--target', required=True,
                        help='Target branch (e.g. master branch)')
    parser.add_argument('--subpath', required=True,
                        help='Subpath containing the charts (e.g. system)')

    args = parser.parse_args()

    source_path = mkdtemp()
    target_path = mkdtemp()

    clone_repository(args.repository, args.source, source_path)
    clone_repository(args.repository, args.target, target_path)

    for chart in changed_charts(source_path, target_path, args.subpath):
        with NamedTemporaryFile(suffix='.yaml', mode='w+', delete=False) as f_source, NamedTemporaryFile(suffix='.yaml', mode='w+', delete=False) as f_target:
            render_helm_chart(
                f"{source_path}/{args.subpath}/{chart}", chart, chart, f_source.name)
            render_helm_chart(
                f"{target_path}/{args.subpath}/{chart}", chart, chart, f_target.name)

            diff_result = run(
                ['dyff', 'between', '--omit-header', '--use-go-patch-style',
                    '--color=on', '--truecolor=off', f_target.name, f_source.name],
                capture_output=True,
                text=True,
                check=True
            )

            print(diff_result.stdout)


if __name__ == "__main__":
    main()
