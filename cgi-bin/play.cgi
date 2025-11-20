#!/usr/bin/perl
#
# play.cgi - Serve MP3 files for Cedar Cross Band practice songs
# Validates requested file exists in database and serves with proper headers
#
# Author: Generated for Cedar Cross Band
# Create Date: September 2025
# Updated: November 2025 to revise configuration variables to point to practice directory
#

use strict;
use warnings;
use CGI qw(:standard);
use File::Basename;

# Configuration
my $home_dir = $ENV{HOME} || "/home/churchd";
my $SONGLIST_FILE = "$home_dir/private_html/CedarCrossBand/songlist.txt";
my $MP3_DIR = "$home_dir/private_html/CedarCrossBand/mp3s";

# CGI object
my $cgi = CGI->new;

# Get requested song parameter
my $requested_song = $cgi->param('song') || '';

# Clean and validate the parameter
$requested_song =~ s/^\s+|\s+$//g;  # Trim whitespace

# Security check: ensure filename doesn't contain path traversal attempts
if ($requested_song =~ /\.\./ || $requested_song =~ /\//) {
    print_error("Invalid filename: path traversal not allowed");
    exit 1;
}

# Check if parameter is provided
if ($requested_song eq '') {
    print_error("No song specified");
    exit 1;
}

# Verify the song exists in the database
unless (song_exists_in_database($requested_song)) {
    print_error("Song not found in database: $requested_song");
    exit 1;
}

# Build full path to MP3 file
my $mp3_path = "$MP3_DIR/$requested_song";

# Verify the file actually exists on disk
unless (-f $mp3_path && -r $mp3_path) {
    print_error("Song file not found or not readable: $requested_song");
    exit 1;
}

# Get file size for Content-Length header
my $file_size = -s $mp3_path;

# Get just the filename without path for content disposition
my $safe_filename = basename($requested_song);
$safe_filename =~ s/[^A-Za-z0-9._-]/_/g;  # Sanitize filename

# Check for Range header (for seeking support)
my $range_header = $ENV{HTTP_RANGE} || '';
my $start = 0;
my $end = $file_size - 1;
my $is_range_request = 0;

if ($range_header =~ /^bytes=(\d+)-(\d*)$/) {
    $is_range_request = 1;
    $start = $1;
    $end = $2 ne '' ? $2 : $file_size - 1;
    
    # Validate range
    $start = 0 if $start < 0;
    $end = $file_size - 1 if $end >= $file_size;
    $start = $end if $start > $end;
}

my $content_length = $end - $start + 1;

# Open file
open my $fh, '<:raw', $mp3_path or do {
    print STDERR "Failed to open $mp3_path: $!\n";
    exit 1;
};

# Seek to start position if range request
if ($is_range_request && $start > 0) {
    seek($fh, $start, 0);
}

# Send appropriate HTTP headers
if ($is_range_request) {
    # Send 206 Partial Content response
    print "Status: 206 Partial Content\r\n";
    print "Content-Type: audio/mpeg\r\n";
    print "Content-Length: $content_length\r\n";
    print "Content-Range: bytes $start-$end/$file_size\r\n";
    print "Accept-Ranges: bytes\r\n";
    print "Content-Disposition: inline; filename=\"$safe_filename\"\r\n";
    print "Cache-Control: public, max-age=3600\r\n";
    print "\r\n";
} else {
    # Send normal 200 OK response
    print $cgi->header(
        -type => 'audio/mpeg',
        -Content_Length => $file_size,
        -Content_Disposition => "inline; filename=\"$safe_filename\"",
        -Cache_Control => 'public, max-age=3600',
        -Accept_Ranges => 'bytes'
    );
}

# Stream the requested portion of the file
my $buffer;
my $chunk_size = 8192;  # 8KB chunks
my $bytes_to_send = $content_length;
my $bytes_sent = 0;

while ($bytes_sent < $bytes_to_send) {
    my $bytes_to_read = $chunk_size;
    if ($bytes_sent + $bytes_to_read > $bytes_to_send) {
        $bytes_to_read = $bytes_to_send - $bytes_sent;
    }
    
    my $bytes_read = read($fh, $buffer, $bytes_to_read);
    last unless $bytes_read;
    
    print $buffer;
    $bytes_sent += $bytes_read;
}

close $fh;

exit 0;

#
# Subroutines
#

sub song_exists_in_database {
    my $filename = shift;
    
    unless (-r $SONGLIST_FILE) {
        return 0;  # Can't read database
    }
    
    open my $fh, '<', $SONGLIST_FILE or return 0;
    
    while (my $line = <$fh>) {
        chomp $line;
        next if $line =~ /^#/ || $line =~ /^\s*$/;  # Skip comments and empty lines
        
        my ($db_filename) = split /\|/, $line, 2;
        next unless defined $db_filename;
        
        $db_filename =~ s/^\s+|\s+$//g;
        
        if ($db_filename eq $filename) {
            close $fh;
            return 1;  # Found it
        }
    }
    
    close $fh;
    return 0;  # Not found
}

sub print_error {
    my $message = shift;
    my $safe_message = html_escape($message);
    
    print $cgi->header(-type => 'text/html', -charset => 'utf-8', -status => '404 Not Found');
    
    print <<EOF;
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Song Not Found - Cedar Cross Band</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
            background-color: #f8f9fa;
        }
        .error-box {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #e74c3c;
        }
        h1 {
            color: #e74c3c;
            margin-bottom: 20px;
        }
        p {
            color: #555;
            margin-bottom: 20px;
        }
        a {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
        }
        a:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="error-box">
        <h1>Song Not Found</h1>
        <p><strong>$safe_message</strong></p>
        <p>The requested song could not be played. It may have been removed or the link may be incorrect.</p>
        <div>
            <a href="../CedarCrossBand/">Return to Home</a>
            <a href="../cgi-bin/browse.cgi">Browse Songs</a>
        </div>
    </div>
</body>
</html>
EOF
}

sub html_escape {
    my $text = shift;
    $text =~ s/&/&amp;/g;
    $text =~ s/</&lt;/g;
    $text =~ s/>/&gt;/g;
    $text =~ s/"/&quot;/g;
    $text =~ s/'/&#39;/g;
    return $text;
}
