"""This file compiles all the provided post templates"""

from os import mkdir, path
from re import finditer, MULTILINE, sub
from shutil import rmtree

from glob import glob
from jinja2 import Environment, FileSystemLoader

from wotw_highlighter import Block

POSTS_DIR = path.dirname(__file__)
ROOT_DIR = path.dirname(POSTS_DIR)
BUILD_DIR = path.join(POSTS_DIR, 'build')
TEMPLATE_DIR = path.join(POSTS_DIR, 'templates')

rmtree(BUILD_DIR, ignore_errors=True)
mkdir(BUILD_DIR)


def highlight_block(content, **kwargs):
    """Highlights a block via wotw-highlighter"""
    blob = Block(content, inline_css=True, **kwargs)
    return blob.highlighted_blob


def source_branch_graph(section):
    """Sources a generated git log --graph"""
    with open(path.join('script-output', "%s.html" % section)) as graph_source:
        graph = graph_source.read()
    return graph


def link_header(matched_line, used_headlines):
    """Creates a Markdown TOC link"""
    headline = matched_line.group(2)
    cleaned_headline = sub('[^a-z]', '', headline.lower())
    if cleaned_headline in used_headlines:
        used_headlines[cleaned_headline] += 1
        cleaned_headline += str(used_headlines[cleaned_headline])
    else:
        used_headlines[cleaned_headline] = 0
    return "%s[%s](#%s)%s" % (
        matched_line.group(1),
        headline,
        cleaned_headline,
        matched_line.group(3)
    )


def render_single_post(post_basename, jinja_to_use):
    """Renders a specific post file with the provided environment"""
    template = jinja_to_use.get_template(post_basename)
    pre_toc = template.render(
        current_tag=path.splitext(post_basename)[0].replace('.md', '')
    )
    return pre_toc.strip().encode('utf-8')


def build_post_toc(post_content):
    """Builds a Ghost-compatible TOC"""
    no_code_blocks = sub(r'```[\s\S]*?```', '', post_content)
    generated_toc = ""
    used_headlines = dict()
    for matched_header_line in finditer(r'^##(#*)\s*(.*)$', no_code_blocks, MULTILINE):
        headline = matched_header_line.group(2)
        cleaned_headline = sub('[^a-z]', '', headline.lower())
        if cleaned_headline in used_headlines:
            used_headlines[cleaned_headline] += 1
            cleaned_headline += str(used_headlines[cleaned_headline])
        else:
            used_headlines[cleaned_headline] = 0
        generated_toc += "%s- [%s](#%s)\n" % (
            sub('#', '  ', matched_header_line.group(1)),
            headline,
            cleaned_headline
        )
    finalized_toc = sub(
        r'[^\n]*<!--\s*?wotw_toc\s*?-->[^\n]*',
        generated_toc,
        post_content
    )
    return finalized_toc


def strip_extra_whitespace(contents):
    """Removes uncessary whitespace"""
    contents = sub(r'\n\n+', '\n\n', contents)
    contents = sub(r'\n\n```\n\n', '\n```\n\n', contents)
    return contents


def fully_compile_single_post(post_path, jinja_to_use):
    """Run all the steps to compile a single post"""
    post_basename = path.basename(post_path)
    initial_pass = render_single_post(post_basename, jinja_to_use)
    toc_pass = build_post_toc(initial_pass)
    final_pass = strip_extra_whitespace(toc_pass)
    output_filename = path.join(BUILD_DIR, post_basename.replace('.j2', ''))
    with file(output_filename, 'w+') as built_file:
        built_file.write(final_pass)


def compile_all_posts():
    """Create the Jinja environment, load the posts, and build everything"""
    jinja_env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR)
    )

    jinja_env.globals['highlight_block'] = highlight_block
    jinja_env.globals['source_branch_graph'] = source_branch_graph

    for post_filename in glob(path.join(TEMPLATE_DIR, 'post-*.j2')):
        fully_compile_single_post(post_filename, jinja_env)

compile_all_posts()
