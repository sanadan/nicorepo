#!/usr/bin/env ruby

require 'bundler/setup'
Bundler.require
require 'rss'

NICOREPO_URI = 'http://www.nicovideo.jp/my/top'

config = Pitcgi.get( 'www.nicovideo.jp', :require => {
  'mail' => 'mail address or phone number',
  'password' => 'password',
  'token' => 'auto' } )
nico = Niconico.new( :mail => config[ 'mail' ], :password => config[ 'password' ], :token => config[ 'token' ] )
nico.login
config[ 'token' ] = nico.token
Pitcgi.set( 'www.nicovideo.jp', :data => config )

feed_items = []
page = nico.agent.get( NICOREPO_URI )
page.search( '.log-content' ).each do |data|
  item = {}
  item[ :title ] = data.at( '.log-body' ).text.gsub( /[\t\r\n]/, '' )
  item[ :link ] = data.at( '.log-target a' ).attribute( 'href' )
  body = data.dup
  body.at( '.nicoru-positioned' ).remove
  body.at( '.log-reslist' ).remove
  body.at( '.log-footer' ).remove
  body.children.each do |child|
    child.remove if child.comment?
  end
  body.at( '.log-details' ).children.each do |child|
    child.remove if child.comment?
  end
  img = body.at( '.log-details img' )
  img[ 'src' ] = img[ 'data-src' ]
  img.delete( 'data-src' )
  img[ 'align' ] = 'left'
#  item[ :body ] = body.inner_html.gsub( /\t/, '' ).gsub( /^[ \t]*[\r\n]+/, '' )
  item[ :body ] = body.inner_html.gsub( /[\t\r\n]/, '' )
  item[ :time ] = data.search( '.relative' ).attribute( 'datetime' )

  feed_items << item

=begin
  print "title: " + item[ :title ] + "\n"
  print "link: " + item[ :link ] + "\n"
  print "body: " + item[ :body ] + "\n"
  print "time: " + item[ :time ] + "\n"
=end
end

feed = RSS::Maker.make( 'atom' ) do |maker|
  maker.channel.about = 'http://www.nicovideo.jp/my/top'
  maker.channel.title = 'ニコレポ'
  maker.channel.description = 'ニコレポのフィードです'
  maker.channel.link = 'http://www.nicovideo.jp'
  maker.channel.updated = Time.now
  maker.channel.author = 'sanadan'
  feed_items.each do |data|
    item = maker.items.new_item
    item.link = data[ :link ]
    item.title = data[ :title ]
    item.date = data[ :time ]
    item.content.content = data[ :body ]
    item.content.type = 'html'
  end
end

begin
print "Content-Type: application/atom+xml; charset=UTF-8\n"
print "\n"
print feed
end

