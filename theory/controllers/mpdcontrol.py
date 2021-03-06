# theory MPD client
# Copyright (C) 2008  Ryan Roemmich <ralfonso@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import mpd

from pylons import request, response, session
from pylons import tmpl_context as c
from pylons import app_globals as g
from pylons.controllers.util import abort, redirect_to
from pylons.decorators import jsonify

from mpd import CommandError

from theory.lib.base import BaseController, render

log = logging.getLogger(__name__)

class MpdcontrolController(BaseController):
    requires_auth = True

    @jsonify
    def status(self):
        """ 
        this is the status data that the main indexes calls on an interval.
        uses the pylons @jsonify decorator to turn the output into something
        that can be parsed by JQuery's getJSON() function
        """
            
        m = g.p.connect()
        current = m.currentsong()
        status = m.status()
        m.close()

        return dict(track=current,status=status)

    @jsonify
    def fs_status(self):
        """ 
        similar to status() but includes a forward-looking playlist 
        for the fullscreen widget
        """

        try:
            m = g.p.connect()
        except ConnectionClosed:
            return render('/null.html')

        status = m.status()
        current = m.currentsong()
        playlist = m.playlistinfo()

        track = 0
        found_current = False
        remaining_playlist = []

        for pl in playlist:
            if found_current:
                remaining_playlist.append(pl)

            if 'id' in current:
                if pl['id'] == current['id']:
                    found_current = True
           
            track += 1

        m.close()
        return dict(status=status,current=current,playlist=remaining_playlist)

    def setvolume(self,id):
        m = g.p.connect()

        try:
            volume = id
            m.setvol(volume)
        except ValueError:
            pass

        m.close()

    def seek(self,id,val):
        m = g.p.connect()
        try:
            id = id
            pos = val
            m.seekid(id,pos)
        except ValueError:
            pass

        m.close()

    def stop(self):
        m = g.p.connect()
        m.stop()
        m.close()
    
    def previous(self):
        m = g.p.connect()
        m.previous()
        m.close()
    
    def next(self):
        m = g.p.connect()
        m.next()
        m.close()

    def play(self):
        m = g.p.connect()
        status = m.status()
        if status['state'] == 'play':
            m.pause()
        else:
            m.play()
        m.close()

    def pause(self):
        m = g.p.connect()
        m.pause()
        m.close()

    def reorderplaylist(self):
        tracklist = request.POST.getall('track[]')
        m = g.p.connect()

        iter = 0

        for t in tracklist:
            parts = t.split(':')
            if iter != parts[1]:
                m.moveid(parts[0],iter)
                
            iter += 1
        m.close()

    def addtoplaylist(self):
        file = request.POST.get('file').encode('utf-8')

        m = g.p.connect()
        m.add(file)
        m.close()

    def addalbumtoplaylist(self):
        artist = request.GET.get('artist').encode('utf-8')
        album = request.GET.get('album').encode('utf-8')

        m = g.p.connect()
        tracks = m.tracks(artist,album)

        m.command_list_ok_begin()
        for t in tracks:
            m.add(t['file'])

        m.command_list_end()
        m.close()

    def addartistalbums(self):
        artist = request.GET.get('artist').encode('utf-8')

        m = g.p.connect()
        albums = m.albums(artist)

        tracklist = []

        for album in albums:
            tracklist.extend(m.tracks(artist,album))
        
        m.command_list_ok_begin()

        for t in tracklist:
            m.add(t['file'])

        m.command_list_end()
        m.close()


    def addpathtoplaylist(self):
        path = request.POST.get('path').encode('utf-8')

        m = g.p.connect()

        tracklist = []

        lsinfo = m.lsinfo(path)

        for f in lsinfo:
            if 'file' in f:
                tracklist.append(f)
        
        m.command_list_ok_begin()

        for t in tracklist:
            m.add(t['file'])

        m.command_list_end()  
        m.close()

    def removetrack(self,id):
        m = g.p.connect()
        try:
            m.deleteid(id)
        except CommandError,e: # exception if the track to be removed doesn't exist
            return str(e)
        finally:
            m.close()

    def removemultipletracks(self,id):
        m = g.p.connect()
        for id in id.split(','):
            if id:
                try:
                    m.deleteid(id)
                except CommandError,e: # exception if the track to be removed doesn't exist
                    pass

    def playnow(self,id):
        m = g.p.connect()
        try:
            m.playid(id)
            m.play()
        except CommandError,e:
            return str(e)
        finally:
            m.close() 

    def repeat(self,id):
        m = g.p.connect()
        m.repeat(id)
        m.close()

    def random(self,id):
        m = g.p.connect()
        m.random(id)
        m.close()

    def rescan(self):
        m = g.p.connect()
        m.update()

    def clearplaylist(self):
        m = g.p.connect()
        m.clear()
        m.close()
        
    
    def shuffle(self):
        m = g.p.connect()
        m.shuffle()
        m.close()
        
    def trimplaylist(self):
        """ trims the playlist of everything leading up to the currently playing track """
        m = g.p.connect()
        current = m.status()
        playlist = m.playlistinfo()

        if not 'songid' in current:
            return

        if len(playlist) == 0:
            return

        m.command_list_ok_begin()

        for t in playlist:
            if current['songid'] != t['id']:
                self.removetrack(t['id'])
            else:
                break

        m.command_list_end()
        m.close()

    def playnext(self,id):
        m = g.p.connect()
        current = m.currentsong()
        if not 'pos' in current:
            return
        m.moveid(id,int(current['pos'])+1)
        m.close()

