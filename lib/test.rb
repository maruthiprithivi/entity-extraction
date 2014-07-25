#!/usr/bin/ruby
#
require 'rubygems'
require 'net/http'
require 'cgi'
require 'json'

def get_response(query, output_type, entity_type)
  domain ='http://10.17.208.221:6860'
  path = '/get_entity'
  params = {:query => query, :output_type => output_type, :entity_type => entity_type}
  path = "#{path}?".concat(params.collect { |k,v| "#{k}=#{CGI::escape(v.to_s)}" }.join('&'))
  uri = URI.parse(domain+path)
  st = Net::HTTP.get(uri)
  print st
  puts
  begin
    response = JSON.parse st
    #response = eval(st)
    return response
  rescue SyntaxError => exc
    return ['Error: Bad Request']
  end
end

def change_query(query, output_type, entity_type)
  output = get_response(query, output_type, entity_type)
  result = ''
  location_list = output[-1]
  output = output[0]
  if output.class == Hash
    puts output
    puts     
  else
    for i in (0..output.size)
      if output[i].class == Array
        result = result << '+"' << "#{output[i][0]}" << '" '
      else
        result = result <<  "#{output[i]} " 
      end
    end
  end
  final = ''
  if location_list.size > 0:
    string = '"' + location_list[0] + '"' 
    for i in (1...location_list.size)
      string += ' OR "' + location_list[i] + '"'
    end 
    final = '&fq=title:(' + string + ') OR description:(' + string + ')'
  end
  return result, final
end

query = ARGV[0]
output_type = ARGV[1]
entity_type = ARGV[2]
result, location_string = change_query(query, output_type, entity_type)
puts result
puts location_string



