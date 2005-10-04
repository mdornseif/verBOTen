#!/usr/local/bin/ruby
require 'optparse'

# import into the LuFG CRM

options = { :environment => "development" }

ARGV.options do |opts|
  script_name = File.basename($0)
  opts.banner = "Usage: runner 'puts Person.find(1).name' [options]"

  opts.separator ""

  opts.on("-e", "--environment=name", String,
          "Specifies the environment for the runner to operate under (test/development/production).",
          "Default: development") { |options[:environment]| }

  opts.separator ""

  opts.on("-h", "--help",
          "Show this help message.") { puts opts; exit }

  opts.parse!
end

ENV["RAILS_ENV"] = options[:environment]

require File.dirname(__FILE__) + '/config/environment'

require 'find'
#require 'CGI'

Find.find('verBOTen/datadir') do |path|
    if FileTest.directory?(path)
      if File.basename(path)[0] == ?.
        Find.prune       # Don't look any further into this directory.
      else
        next
      end
    else
      hostn = File.basename(path).downcase
      print "*** #{hostn}\n"
      File.new(path).each do |l| 
        l.strip!
        l = CGI::unescape(l)
        host = ArchiveHost.get_host(hostn)
        print "#{hostn} #{l} \n"
        host.save
        disallow = ArchiveRobotsDisallow.find(:first, :conditions => ['archive_host_id = ? and path = ?', 
                                                                      host.id, l])
        if disallow.nil?
          disallow = ArchiveRobotsDisallow.new
          disallow.path = l
          disallow.archive_host_id = host.id
          disallow.save
        end
      end
    end
  end
  