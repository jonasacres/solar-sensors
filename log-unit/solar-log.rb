#!/usr/bin/env ruby

require 'json'
require 'websocket-client-simple'
require 'sqlite3'
require 'time'

def open_db(path)
  db_existed = File.exists?(path)
  db = SQLite3::Database.new path

  unless db_existed then
    db.execute <<-SQL
      create table solar (
        record_id integer primary key autoincrement,
        time_inserted_epoch integer,
        time_inserted_str varchar(32),
        
        photo_v real,
        solar_v real,
        solar_power_mw real
      );
    SQL

    db.execute <<-SQL
      create index time_index on solar (time_inserted_epoch)
    SQL
  end

  db
end

$db_file = "solar.db"
$db = open_db("solar.db")
$url = IO.read("http-keystore-url").strip
$db.execute("select time_inserted_str from solar order by time_inserted_epoch desc limit 1") { |row| $last_update = row[:time_inserted_str] }
ws = WebSocket::Client::Simple.connect $url

puts "Starting at #{Time.now.strftime("%Y-%m-%d %H:%M:%S %Z")}"
puts "Logging to #{File.expand_path($db_file)}"
puts "Connecting to #{$url}"
if $last_update
  puts "Last update was #{$last_update}"
else
  puts "No data on file"
end
puts ""

ws.on :message do |msg|
  begin
    top = JSON.parse(msg.to_s, symbolize_names:true)
    if $last_update == top[:"Last-Modified"]
      puts "skipping update; already saw update for #{$last_update}"
      next
    end

    $last_update = top[:"Last-Modified"]
    data = JSON.parse(top[:data], symbolize_names:true)
    ts = Time.parse(top[:"Last-Modified"])

    puts data
    puts Time.now.strftime("%Y-%m-%d %H:%M:%S %Z")
    puts "  Update time: #{$last_update}"
    puts "Photo voltage: #{data[:photo_v]}V"
    puts "Solar voltage: #{data[:solar_v]}V"
    puts "  Solar power: #{data[:solar_power_mw]}mW"
    puts ""

    insert_keys = [ :photo_v, :solar_v, :solar_power_mw ]
    $db.execute "INSERT INTO solar (time_inserted_epoch, time_inserted_str, photo_v, solar_v, solar_power_mw) VALUES (?, ?, ?, ?, ?)",
       ts.to_i, top[:"Last-Modified"], data[:photo_v], data[:solar_v], data[:solar_power_mw]
  rescue Exception => exc
    STDERR.puts "Caught exception processing update: #{exc.class} #{exc}"
    STDERR.puts exc.backtrace.join("\n")
  end
end

ws.on :open do
  puts "Websocket opened to #{$url}"
end

ws.on :close do |e|
  STDERR.puts e
  exit 1
end

ws.on :error do |e|
  STDERR.puts e
end

loop do
  sleep 3600
end
