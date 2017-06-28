#!/usr/bin/env ruby

DEBUG = false 
NICO_PIT = 'www.nicovideo.jp'
NICOREPO_API = 'http://www.nicovideo.jp/api/nicorepo/timeline/my/all?client_app=pc_myrepo'
STYLE = ''
User = Struct.new( :name, :thumbnail )
Ranking = Struct.new( :highest, :type, :span, :category )

require 'bundler'
Bundler.require
require 'rss/maker'

def user( data )
  user = data[ 'senderNiconicoUser' ]
  ret = User.new
  ret.name = user[ 'nickname' ]
  ret.thumbnail = user[ 'icons' ][ 'tags' ][ 'defaultValue' ][ 'urls' ][ 's50x50' ]
  return ret
end

def ranking( data )
  ranking = data[ 'actionLog' ]
  ret = Ranking.new
  ret.highest = ranking[ 'newHighestRanking' ]
  ret.type = ranking[ 'rankingType' ]
  ret.span = ranking[ 'rankingSpan' ]
  ret.category = ranking[ 'rankingCategory' ]
  return ret
end

def thumbnail( url )
  return link_to( '<img class="nicorepo" align="left" src="' + url + '">', url )
end

def link_to( content, url )
  return '<a href="' + url + '">' + content + '</a>'
end

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
  nicorepo = JSON.parse( json )
  File.write( 'nicorepo.json', JSON.pretty_generate( nicorepo ) ) if DEBUG
  nicorepo[ 'data' ].each do |data|
    item = {}
    item[ :id ] = data[ 'id' ]
    item[ :time ] = data[ 'createdAt' ]
    item[ :body ] = STYLE
    case data[ 'topic' ]
    when 'nicovideo.user.video.upload'
      video = data[ 'video' ]
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      user = user( data )
      item[ :body ] += thumbnail( video[ 'thumbnailUrl' ][ 'normal' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんが ' + video[ 'title' ] + ' を投稿しました。'
    when 'nicovideo.user.mylist.add.video', 'nicovideo.user.temporary_mylist.add.video'
      video = data[ 'video' ]
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      user = user( data )
      mylist = {}
      if data[ 'topic' ] =~ /temporary_mylist/
        mylist[ 'name' ] = 'とりあえずマイリスト'
      else
        mylist = data[ 'mylist' ]
      end
      item[ :body ] += thumbnail( video[ 'thumbnailUrl' ][ 'normal' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんが ' + video[ 'title' ] + ' をマイリスト ' + mylist[ 'name' ] + ' に登録しました。'
    when 'nicovideo.user.community.video.add'
      video = data[ 'memberOnlyVideo' ]
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      user = user( data )
      community = data[ 'communityForFollower' ]
      item[ :body ] += thumbnail( video[ 'thumbnailUrl' ][ 'normal' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんが ' + video[ 'title' ] + ' をコミュニティ ' + community[ 'name' ] + ' に追加しました。'
    when 'nicovideo.user.video.kiriban.play'
      video = data[ 'video' ]
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      user = user( data )
      kiriban = data[ 'actionLog' ][ 'kiriban' ].to_s
      item[ :body ] += thumbnail( video[ 'thumbnailUrl' ][ 'normal' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんの ' + video[ 'title' ] + ' が ' + kiriban + '再生されました。'
    when 'nicovideo.user.video.update_highest_rankings'
      video = data[ 'video' ]
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      user = user( data )
      ranking = ranking( data )
      item[ :body ] += thumbnail( video[ 'thumbnailUrl' ][ 'normal' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんの ' + video[ 'title' ] + ' が ' + ranking.category + ' で ' + ranking.span + ' ' + ranking.highest.to_s + '位になりました。'
    when 'nicovideo.user.video.advertise'
      video = data[ 'video' ]
      item[ :title ] = video[ 'title' ]
      item[ :link ] = 'http://www.nicovideo.jp/watch/' + video[ 'videoWatchPageId' ]
      user = user( data )
      uad = data[ 'uad' ]
      item[ :body ] += thumbnail( video[ 'thumbnailUrl' ][ 'normal' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんが ' + video[ 'title' ] + ' を ニコニ広告 で宣伝しました。'
    when 'live.user.program.onairs', 'live.user.program.reserve'
      live = data[ 'program' ]
      item[ :title ] = live[ 'title' ]
      item[ :link ] = 'http://live.nicovideo.jp/watch/' + live[ 'id' ]
      user = user( data )
      community = data[ 'community' ]
      item[ :body ] += thumbnail( live[ 'thumbnailUrl' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんがコミュニティ ' + community[ 'name' ]
      if data[ 'topic' ].split( '.' ).last == 'onair'
        item[ :body ] += ' で生放送を開始しました。'
      else
        item [:body ] += ' で ' + live[ 'beginAt' ] + ' からの生放送を予約しました。'
      end
    when 'live.channel.program.onairs'
      live = data[ 'program' ]
      item[ :title ] = live[ 'title' ]
      item[ :link ] = 'http://live.nicovideo.jp/watch/' + live[ 'id' ]
      channel = data[ 'senderChannel' ]
      item[ :body ] += thumbnail( live[ 'thumbnailUrl' ] ) + ' ' + thumbnail( channel[ 'thumbnailUrl' ] ) + ' チャンネル ' + channel[ 'name' ] + ' で生放送が開始されました。'
    when 'nicoseiga.user.illust.upload'
      illust = data[ 'illustImage' ]
      item[ :title ] = illust[ 'title' ]
      item[ :link ] = illust[ 'urls' ][ 'pcUrl' ]
      user = user( data )
      item[ :body ] += thumbnail( illust[ 'thumbnailUrl' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんがイラスト ' + illust[ 'title' ] + ' を投稿しました。'
    when 'nicoseiga.user.illust.clip'
      illust = data[ 'illustImage' ]
      item[ :title ] = illust[ 'title' ]
      item[ :link ] = illust[ 'urls' ][ 'pcUrl' ]
      user = user( data )
      item[ :body ] += thumbnail( illust[ 'thumbnailUrl' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんがイラスト ' + illust[ 'title' ] + ' をクリップしました。'
    when 'nicoseiga.user.manga.episode.upload'
      manga = data[ 'mangaEpisode' ]
      item[ :title ] = manga[ 'title' ]
      item[ :link ] = manga[ 'urls' ][ 'pcUrl' ]
      user = user( data )
      item[ :body ] += thumbnail( manga[ 'thumbnailUrl' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんがマンガ ' + manga[ 'title' ] + ' を投稿しました。'
    when 'nicoseiga.user.manga.content.favorite'
      manga = data[ 'mangaContent' ]
      item[ :title ] = manga[ 'title' ]
      item[ :link ] = manga[ 'urls' ][ 'pcUrl' ]
      user = user( data )
      item[ :body ] += thumbnail( manga[ 'thumbnailUrl' ] ) + ' ' + thumbnail( user.thumbnail ) + ' ' + user.name + ' さんがマンガ ' + manga[ 'title' ] + ' をお気に入りしました。'
    else
      item[ :title ] = '知らないレポート形式です。'
      item[ :body ] = JSON.pretty_generate( data )
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

