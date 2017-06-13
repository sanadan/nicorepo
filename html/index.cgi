#!/usr/bin/env ruby

NICO_PIT = 'www.nicovideo.jp'
NICOREPO_URI = 'http://www.nicovideo.jp/my/top'
THUMBNAIL_TAG = 'data-original'
NICOREPO_API = 'http://www.nicovideo.jp/api/nicorepo/timeline/my/all?client_app=pc_myrepo'

require 'bundler'
Bundler.require
require 'rss/maker'

def main
  config = Pitcgi.get( NICO_PIT, :require => {
    'mail' => 'mail address or phone number',
    'password' => 'password',
    'token' => 'auto' } )
  nico = Niconico.new( :mail => config[ 'mail' ], :password => config[ 'password' ], :token => config[ 'token' ] )
  nico.login
  config[ 'token' ] = nico.token
  Pitcgi.set( NICO_PIT, :data => config )

  json = nico.agent.get( NICOREPO_API ).body
File.write( 'o.json', json )
  nicorepo = JSON.parse( json )
  nicorepo[ 'data' ].each do |data|
    item = {}
    item[ :id ] = data[ 'id' ]
    item[ :time ] = data[ 'createdAt' ]
    item[ :title ] = ''
    user = data[ 'senderNiconicoUser' ]
    item[ :body ] = '<img src="' + user[ 'icons' ][ 'tags' ][ 'defaultValue' ][ 'urls' ][ 's50x50' ] + '">'
    item[ :body ] += user[ 'nickname' ] + ' さんが'
    video = data[ 'video' ]
    video ||= data[ 'memberOnlyVideo' ]
    if video
      if data[ 'video' ]
        item[ :body ] += '動画を投稿しました。<br>'
      else
        community = data[ 'communityForFollower' ]
        item[ :body ] += 'コミュニティ ' + community[ 'name' ] + ' に動画を追加しました。<br>'
      end
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      item[ :body ] += '<img src="' + video[ 'thumbnailUrl' ][ 'normal' ] + '">'
    elsif data[ 'illustImage' ]
      image = data[ 'illustImage' ]
      item[ :title ] = image[ 'title' ]
      item[ :body ] += 'イラストを投稿しました。<br>'
      item[ :body ] += '<img src="' + image[ 'thumbnailUrl' ] + '">'
    elsif data[ 'program' ]
      program = data[ 'program' ]
      item[ :title ] = program[ 'title' ]
      community = data[ 'community' ]
      item[ :body ] += 'コミュニティ ' + community[ 'name' ] + ' で生放送を開始しました。<br>'
      item[ :body ] += '<img src="' + program[ 'thumbnailUrl' ] + '">'
    else
      item[ :body ] += data.to_s
    end
    
    @feed_items << item
  end
end

@feed_items = []
begin
  main
rescue
  data = {}
  data[ :id ] = Time.now.strftime( '%Y%m%d%H%M%S' )
  data[ :title ] = $!.to_s
  data[ :time ] = Time.now
  data[ :body ] = $!.to_s
  $!.backtrace.each do |trace|
    data[ :body ] += '<br>'
    data[ :body ] += trace
  end
  @feed_items << data
end

feed = RSS::Maker.make( 'atom' ) do |maker|
  maker.channel.about = 'nicorepo_feed'
  maker.channel.title = 'ニコレポ'
  maker.channel.description = 'ニコレポのフィードです'
  maker.channel.link = 'http://www.nicovideo.jp/my/top'
  maker.channel.updated = Time.now
  maker.channel.author = 'sanadan'
  @feed_items.each do |data|
    item = maker.items.new_item
    item.id = data[ :id ] if data[ :id ]
    item.link = data[ :link ] if data[ :link ]
    item.title = data[ :title ]
    item.date = data[ :time ]
    item.content.content = data[ :body ]
    item.content.type = 'html'
  end
end

print "Content-Type: application/atom+xml; charset=UTF-8\n"
print "\n"
print feed

