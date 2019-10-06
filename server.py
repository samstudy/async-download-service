import asyncio
from aiohttp import web
import datetime
import aiofiles
import os
import argparse
import functools


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('photos_dir', type=str,help='Photos folder')
    parser.add_argument('log', type=int,help='enable/disable debug log')
    parser.add_argument('delay', type=int, help='set delay in seconds')
    return parser.parse_args()


async def archivate(request,photos_dir,is_enable_log,delay):
    folder = photos_dir + request.match_info['archive_hash']
    if not os.path.exists(folder):
        return web.HTTPNotFound(text='Архив не существует или был удален')
    response = web.StreamResponse()
    response.headers['Content-Disposition'] = 'attachment; filename="archive.zip"'
    await response.prepare(request)
    zip_process = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', folder,
        stdout=asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE)
    try:
        while True:
            archive_chunk = await zip_process.stdout.readline()
            if bool(log_enabled):
                logging.debug('Sending archive chunk ...')
            if not archive_chunk:
                break
            await response.write(archive_chunk)
            await asyncio.sleep(delay)
    finally:
        zip_process.kill()
        response.force_close
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def main():
    params = get_args()
    app = web.Application()
    photos_folder = params.photos_dir
    log_enabled = params.log
    delay = params.delay
    chunk_archivate = functools.partial(archivate,photos_folder,log_enabled,delay )
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', chunk_archivate),
        ])
    web.run_app(app)


if __name__ == '__main__':
    main()