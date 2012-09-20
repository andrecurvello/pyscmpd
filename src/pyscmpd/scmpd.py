##
# This file is part of the carambot-usherpa project.
#
# Copyright (C) 2012 Stefan Wendler <sw@kaltpost.de>
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
##

'''
This file is part of the pyscmpd project.
'''

import logging
import mpdserver
import soundcloud

import pyscmpd.scprovider as provider 
import pyscmpd.gstplayer as gstplayer 

class ScMpdServerDaemon(mpdserver.MpdServerDaemon):

	scp 	= None
	scroot  = None
	player	= None
 
	def __init__(self, favorites, serverPort = 9900):
		
		provider.ResourceProvider.favorites = favorites 
 
		ScMpdServerDaemon.player 	= gstplayer.GstPlayer() 
		ScMpdServerDaemon.scp 		= provider.ResourceProvider()
		ScMpdServerDaemon.scroot 	= ScMpdServerDaemon.scp.getRoot()

		mpdserver.MpdServerDaemon.__init__(self, serverPort)

		self.requestHandler.RegisterCommand(mpdserver.Outputs)
		self.requestHandler.RegisterCommand(Play)
		self.requestHandler.RegisterCommand(PlayId)
		self.requestHandler.RegisterCommand(Stop)
		self.requestHandler.RegisterCommand(Pause)
		self.requestHandler.RegisterCommand(Next)
		self.requestHandler.RegisterCommand(Previous)
		self.requestHandler.RegisterCommand(LsInfo)
		self.requestHandler.RegisterCommand(Add)
		self.requestHandler.RegisterCommand(AddId)
		self.requestHandler.RegisterCommand(Clear)
		self.requestHandler.RegisterCommand(Status)
		self.requestHandler.RegisterCommand(CurrentSong)
		self.requestHandler.RegisterCommand(SetVol)
		self.requestHandler.RegisterCommand(mpdserver.Move)
		self.requestHandler.RegisterCommand(mpdserver.MoveId)

		self.requestHandler.Playlist = MpdPlaylist

class Play(mpdserver.Play):

	def handle_args(self, songPos=0):

		ScMpdServerDaemon.player.play(songPos)

class PlayId(mpdserver.PlayId):

	def handle_args(self, songId=0):

		logging.debug("Playid %d" % songId)

		ScMpdServerDaemon.player.playId(songId)

class SetVol(mpdserver.SetVol):

	def handle_args(self, volume):

		ScMpdServerDaemon.player.setVolume(volume)

class Stop(mpdserver.Command):

	def handle_args(self):

		ScMpdServerDaemon.player.stop()

class Next(mpdserver.Command):

	def handle_args(self):

		ScMpdServerDaemon.player.next()

class Previous(mpdserver.Command):

	def handle_args(self):

		ScMpdServerDaemon.player.previous()

class Pause(mpdserver.Command):

	def handle_args(self):

		ScMpdServerDaemon.player.pause()

class Clear(mpdserver.Command):

	def handle_args(self):

		logging.info("Clear playlist")

		ScMpdServerDaemon.player.stop()
		ScMpdServerDaemon.player.delAllChildren()

class CurrentSong(mpdserver.CurrentSong):

    def songs(self): 

		t = ScMpdServerDaemon.player.currentSong()

		if t == None:
			return []

		s = mpdserver.MpdPlaylistSong(
			playlistPosition = ScMpdServerDaemon.player.currentSongNumber,
			artist = t.getMeta("Artist").encode('ASCII', 'ignore'), 
			title = t.getMeta("Title").encode('ASCII', 'ignore'), 
			file = t.getMeta("file").encode('ASCII', 'ignore'),
			time = "%d" % (t.getMeta("Time") / 1000),
			songId = t.getId())

		return [s]

class LsInfo(mpdserver.LsInfo):

	currdir = None
	directory = None

	def handle_args(self, directory="/"):

		logging.info("List directory [%s]" % directory)

		if directory == "/":
			self.directory = None
		else:
			self.directory = directory
		
	def items(self):

		i = []
		path = ""

		if self.directory == None:
			r = ScMpdServerDaemon.scroot.getAllChildren()
		else:

			if self.directory.startswith("favorites/") or self.directory.startswith("random/"):
				(d, s, f) = self.directory.partition("/")
				r = ScMpdServerDaemon.scroot.getChildByName(d).getChildByName(f)
			else:
				r = ScMpdServerDaemon.scroot.getChildByName(self.directory)

			if r == None:
				return i	

			path = r.getName()
			r = r.getAllChildren()

		for e in r:

			logging.debug("LsInfo sending item: %s/%s" % (path, e.__str__()))

			if e.getType() == 1:
				i.append(("directory", e.getMeta("directory")))
			else:
				i.append(("file", e.getMeta("file")))
				i.append(("Artist", e.getMeta("Artist")))
				i.append(("Title", e.getMeta("Title")))
				i.append(("Time", int(e.getMeta("Time") % 1000)))
 
		return i 

class Add(mpdserver.Add):

	def handle_args(self, song):

		logging.info("Adding song [%s] to playlist" % song) 

		(d, s, f) = song.partition("/")

		if d == "favorites" or d == "random":
			(user, s, track) = f.partition("/") 
			u = ScMpdServerDaemon.scroot.getChildByName(d).getChildByName(user)
		else:
			user  = d
			track = f	
			u = ScMpdServerDaemon.scroot.getChildByName(user)

		if u == None:
			logging.error("Could not find directory for [%s]", user)
			return

		t = u.getChildByName(track)

		if t == None:
			logging.error("Track [%s] not found in directory [%s]" % (track, user))
			return

		ScMpdServerDaemon.player.addChild(t)
		
		logging.info("Successfully added song: %s" % t.__str__())

class AddId(mpdserver.AddId):

	uniqueId = 0

	def handle_args(self, song):

		logging.info("Adding song [%s] to playlist" % song) 

		(d, s, f) = song.partition("/")

		if d == "favorites" or d == "random":
			(user, s, track) = f.partition("/") 
			u = ScMpdServerDaemon.scroot.getChildByName(d).getChildByName(user)
		else:
			user  = d
			track = f	
			u = ScMpdServerDaemon.scroot.getChildByName(user)

		if u == None:
			logging.error("Could not find directory for [%s]", user)
			return

		t = u.getChildByName(track)

		if t == None:
			logging.error("Track [%s] not found in directory [%s]" % (track, user))
			return

		ScMpdServerDaemon.player.addChild(t)
		
		self.uniqueId = t.getId()
		
	def items(self):

		# self.uniqueId = self.uniqueId + 1

		return [("id", self.uniqueId)]


class MpdPlaylist(mpdserver.MpdPlaylist):

    def handlePlaylist(self):

		# TODO: only recreate list if player indicates new playlist version

		pl 	= []
		i 	= 0
		c 	= ScMpdServerDaemon.player.getAllChildren()
		l 	= len(c)

		for t in c: 

			s = mpdserver.MpdPlaylistSong(
				playlistPosition = i,
				artist = t.getMeta("Artist").encode('ASCII', 'ignore'), 
				title = t.getMeta("Title").encode('ASCII', 'ignore'), 
				file = t.getMeta("file").encode('ASCII', 'ignore'),
				track = "%d/%d" % (i + 1, l),
				time = "%d" % (t.getMeta("Time") / 1000),
				songId = t.getId())

			i = i + 1

			pl.append(s)

		return pl 

    def version(self):
		return ScMpdServerDaemon.player.playlistVersion 

    def move(self,fromPosition,toPosition):
		ScMpdServerDaemon.player.moveId(fromPosition, toPosition)

    def moveId(self,fromId,toPosition):
		ScMpdServerDaemon.player.moveId(fromId, toPosition)
 
    def delete(self, position):
		ScMpdServerDaemon.player.delete(position)

    def deleteId(self, songId):
		ScMpdServerDaemon.player.deleteId(songId)

class Status(mpdserver.Status):

	def items(self):
  
		if ScMpdServerDaemon.player.playerStatus == "play":
			return self.helper_status_play(
				volume = ScMpdServerDaemon.player.getVolume(),
				elapsedTime = ScMpdServerDaemon.player.elapsedTime(),
				durationTime = ScMpdServerDaemon.player.duration(),
				playlistSongNumber = ScMpdServerDaemon.player.currentSongNumber,
				playlistSongId = ScMpdServerDaemon.player.currentSongId)

		if ScMpdServerDaemon.player.playerStatus == "pause":
			return self.helper_status_pause(
				volume = ScMpdServerDaemon.player.getVolume(),
				elapsedTime = ScMpdServerDaemon.player.elapsedTime(),
				durationTime = ScMpdServerDaemon.player.duration(),
				playlistSongNumber = ScMpdServerDaemon.player.currentSongNumber,
				playlistSongId = ScMpdServerDaemon.player.currentSongId)

		return self.helper_status_stop()