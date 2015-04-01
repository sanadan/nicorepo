#!/usr/bin/env ruby

NICO_PIT = 'www.nicovideo.jp'
NICOREPO_URI = 'http://www.nicovideo.jp/my/top'
THUMBNAIL_TAG = 'data-original'

require 'bundler/setup'
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

  page = nico.agent.get( NICOREPO_URI )
  page.search( '.log-content' ).each do |data|
    item = {}
    item[ :title ] = data.at( '.log-body' ).text.gsub( /[\t\r\n]/, '' )
#    item[ :link ] = data.at( '.log-target a' ).attribute( 'href' )
    link = data.at( '.log-target a' )
    if ( link == nil ) then
      link = data.at( '.log-body a' )
    end
    item[ :link ] = link.attribute( 'href' )
    body = data.dup
    nicoru = body.at( '.nicoru-positioned' )
    nicoru.remove if nicoru
    body.at( '.log-reslist' ).remove
    body.at( '.log-footer' ).remove
    body.children.each do |child|
      child.remove if child.comment?
    end
    body.at( '.log-details' ).children.each do |child|
      child.remove if child.comment?
    end
    img = body.at( '.log-details img' )
    if ( img != nil ) then
      img[ 'src' ] = img[ THUMBNAIL_TAG ]
      img.delete( THUMBNAIL_TAG )
      img[ 'align' ] = 'left'
    end
#  item[ :body ] = body.inner_html.gsub( /\t/, '' ).gsub( /^[ \t]*[\r\n]+/, '' )
    item[ :body ] = body.inner_html.gsub( /[\t\r\n]/, '' )
    item[ :time ] = data.search( '.relative' ).attribute( 'datetime' )

    @feed_items << item

=begin
    print "title: " + item[ :title ] + "\n"
    print "link: " + item[ :link ] + "\n"
    print "body: " + item[ :body ] + "\n"
  print "time: " + item[ :time ] + "\n"
=end
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

