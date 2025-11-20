#!/usr/bin/perl
#
# browse.cgi - Browse and display Cedar Cross Band practice songs
# Handles pagination, sorting, and generates clickable song links
#
# Author: Generated for Cedar Cross Band
# Date: September 2025
#

use strict;
use warnings;
use CGI qw(:standard);
use File::Basename;

# Configuration
my $home_dir = $ENV{HOME} || "/home/churchd";
my $SONGLIST_FILE = "$home_dir/private_html/CedarCrossBand/songlist.txt";
my $MP3_BASE_URL = "/CedarCrossBand/mp3s";
my $CSS_URL = "/~churchd/CedarCrossBand/css/style.css";
my $SONGS_PER_PAGE = 25;

# CGI object
my $cgi = CGI->new;

# Get parameters
my $page = $cgi->param('page') || 1;
my $sort = $cgi->param('sort') || 'title';
my $order = $cgi->param('order') || 'asc';
my $recent = $cgi->param('recent') || 0;  # to handle recent options

# Validate parameters
$page = 1 if $page !~ /^\d+$/ || $page < 1;
$sort = 'title' unless $sort =~ /^(title|date|filename)$/;
$order = 'asc' unless $order =~ /^(asc|desc)$/;
$recent = 0 unless $recent =~ /^[01]$/;  # for recent

# Read and parse song list
my @songs = read_songlist();
# Handle recent mode
if ($recent) {
    # Sort by date descending (newest first) and limit to 15 songs
    @songs = sort { $b->{date} cmp $a->{date} } @songs;
    @songs = splice(@songs, 0, 15) if @songs > 15;
    $sort = 'date';  # Override sort for display purposes
    $order = 'desc';
} else {
    @songs = sort_songs(\@songs, $sort, $order);
}

# Calculate pagination
my $total_songs = scalar @songs;
my $total_pages = int(($total_songs + $SONGS_PER_PAGE - 1) / $SONGS_PER_PAGE);
$page = $total_pages if $page > $total_pages && $total_pages > 0;

my $start_idx = ($page - 1) * $SONGS_PER_PAGE;
my $end_idx = $start_idx + $SONGS_PER_PAGE - 1;
$end_idx = $total_songs - 1 if $end_idx >= $total_songs;

my @page_songs = @songs[$start_idx..$end_idx];

# Generate HTML
print $cgi->header(-type => 'text/html', -charset => 'utf-8');
print_html_page(\@page_songs, $page, $total_pages, $total_songs, $sort, $order);

exit 0;

#
# Subroutines
#

sub read_songlist {
    my @songs = ();
    
    unless (-r $SONGLIST_FILE) {
        return @songs;  # Return empty array if file doesn't exist
    }
    
    open my $fh, '<', $SONGLIST_FILE or return @songs;
    
    while (my $line = <$fh>) {
        chomp $line;
        next if $line =~ /^#/ || $line =~ /^\s*$/;  # Skip comments and empty lines
        
        my ($filename, $title, $date) = split /\|/, $line, 3;
        next unless defined $filename && defined $title;
        
        # Clean up fields
        $filename =~ s/^\s+|\s+$//g;
        $title =~ s/^\s+|\s+$//g;
        $date = $date || 'Unknown';
        $date =~ s/^\s+|\s+$//g;
        
	# Skip if empty after trimming
	next if $filename eq '' || $title eq '';
	
        push @songs, {
            filename => $filename,
            title => $title,
            date => $date
        };
    }
    
    close $fh;
    return @songs;
}
sub sort_songs {
    my ($songs_ref, $sort_field, $sort_order) = @_;
    my @sorted;
    
    if ($sort_field eq 'title') {
        @sorted = sort { 
            my $a_sort = normalize_title_for_sort($a->{title});
            my $b_sort = normalize_title_for_sort($b->{title});
            lc($a_sort) cmp lc($b_sort);
        } @$songs_ref;
    } elsif ($sort_field eq 'date') {
        @sorted = sort { $a->{date} cmp $b->{date} } @$songs_ref;
    } elsif ($sort_field eq 'filename') {
        @sorted = sort { lc($a->{filename}) cmp lc($b->{filename}) } @$songs_ref;
    } else {
        @sorted = @$songs_ref;
    }
    
    @sorted = reverse @sorted if $sort_order eq 'desc';
    
    return @sorted;
}

sub normalize_title_for_sort {
    my $title = shift;
    
    # Remove leading articles for sorting purposes
    # Handle "The ", "A ", "An " (with space after to avoid partial matches)
    $title =~ s/^The\s+//i;
    $title =~ s/^A\s+//i;    # Match only "A " (single letter)
    $title =~ s/^An\s+//i;   # Match only "An " (complete word)
    
    return $title;
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

sub url_encode {
    my $text = shift;
    $text =~ s/([^A-Za-z0-9\-._~])/sprintf("%%%02X", ord($1))/seg;
    return $text;
}

sub print_html_page {
    my ($songs_ref, $current_page, $total_pages, $total_songs, $sort_field, $sort_order) = @_;
    my $header_title = $recent ? "Recently Added Songs" : "Browse All Songs";
    my $song_count_text = $recent ? "Showing last " . scalar(@$songs_ref) . " songs added" : "Showing $total_songs song(s) total";

    
    # Determine opposite sort order for toggle links
    my $opposite_order = $sort_order eq 'asc' ? 'desc' : 'asc';
    
    print <<EOF;
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Browse Songs - Cedar Cross Band</title>
    <meta name="path" content="$SONGLIST_FILE">
    <link rel="stylesheet" href="$CSS_URL">
    <style>
        .browse-header {
            margin: 20px 0;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .sort-controls {
            margin: 10px 0;
            font-size: 0.9em;
        }
        .sort-controls a {
            margin-right: 15px;
            text-decoration: none;
            color: #0066cc;
        }
        .sort-controls a:hover {
            text-decoration: underline;
        }
        .current-sort {
            font-weight: bold;
            color: #333;
        }
        .song-list {
            margin: 20px 0;
        }
        .song-item {
            margin: 8px 0;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .song-item:hover {
            background-color: #f9f9f9;
        }
        .song-title {
            font-size: 1.1em;
            font-weight: bold;
        }
        .song-title a {
            color: #0066cc;
            text-decoration: none;
        }
        .song-title a:hover {
            text-decoration: underline;
        }
        .song-details {
            font-size: 0.85em;
            color: #666;
            margin-top: 3px;
        }
        .pagination {
            margin: 20px 0;
            text-align: center;
        }
        .pagination a, .pagination span {
            display: inline-block;
            padding: 8px 12px;
            margin: 0 2px;
            text-decoration: none;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .pagination a {
            color: #0066cc;
            background-color: #fff;
        }
        .pagination a:hover {
            background-color: #f5f5f5;
        }
        .pagination .current {
            background-color: #0066cc;
            color: white;
            border-color: #0066cc;
        }
        .nav-links {
            margin: 20px 0;
        }
        .nav-links a {
            margin-right: 15px;
            color: #0066cc;
            text-decoration: none;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Cedar Cross Band Practice Songs</h1>
        </header>
        
        <nav class="nav-links">
            <a href="../CedarCrossBand/">&larr; Home</a>
            <a href="../CedarCrossBand/search.html">Search Songs</a>
            <a href="../CedarCrossBand/about.html">About</a>
        </nav>
        
	<div class="browse-header">
            <h2>$header_title</h2>
            <p>$song_count_text</p>
       
            <div class="sort-controls">
                <strong>Sort by:</strong>
EOF

    # Sort control links
    my $title_class = $sort_field eq 'title' ? 'current-sort' : '';
    my $date_class = $sort_field eq 'date' ? 'current-sort' : '';
    my $filename_class = $sort_field eq 'filename' ? 'current-sort' : '';

    my $title_order = $sort_field eq 'title' ? $opposite_order : 'asc';
    my $date_order = $sort_field eq 'date' ? $opposite_order : 'desc';  # Default to newest first
    my $filename_order = $sort_field eq 'filename' ? $opposite_order : 'asc';
    
    print qq{                <a href="?sort=title&order=$title_order" class="$title_class">Title};
    print "^" if $sort_field eq 'title' && $sort_order eq 'asc';
    print " " if $sort_field eq 'title' && $sort_order eq 'desc';
    print "</a>\n";
    
    print qq{                <a href="?sort=date&order=$date_order" class="$date_class">Date Added};
    print "^" if $sort_field eq 'title' && $sort_order eq 'asc';
    print " " if $sort_field eq 'title' && $sort_order eq 'desc';
    print "</a>\n";
    
    print qq{                <a href="?sort=filename&order=$filename_order" class="$filename_class">Filename};
    print "^" if $sort_field eq 'title' && $sort_order eq 'asc';
    print " " if $sort_field eq 'title' && $sort_order eq 'desc';
    print "</a>\n";
    
    print <<EOF;
            </div>
        </div>
EOF


    # Pagination controls (top)
    if ($total_pages > 1) {
        print_pagination($current_page, $total_pages, $sort_field, $sort_order);
    }
    
    # Song list
    print qq{        <div class="song-list">\n};
    
    if (@$songs_ref == 0) {
        print qq{            <p>No songs found.</p>\n};
    } else {
        foreach my $song (@$songs_ref) {
            my $safe_title = html_escape($song->{title});
            my $safe_filename = html_escape($song->{filename});
            my $safe_date = html_escape($song->{date});
            my $encoded_filename = url_encode($song->{filename});
            
            print <<EOF;
            <div class="song-item">
                <div class="song-title">
                    <a href="/~churchd/cgi-bin/play.cgi?song=$encoded_filename">$safe_title</a>
                </div>
                <div class="song-details">
                    File: $safe_filename | Added: $safe_date
                </div>
            </div>
EOF
        }
    }
    
    print qq{        </div>\n};
    
    # Pagination controls (bottom)
    if ($total_pages > 1) {
        print_pagination($current_page, $total_pages, $sort_field, $sort_order);
    }
    
    print <<EOF;
        
        <footer>
            <p><a href="../CedarCrossBand/">&larr; Back to Home</a></p>
        </footer>
    </div>
</body>
</html>
EOF
}

sub print_pagination {
    my ($current_page, $total_pages, $sort_field, $sort_order) = @_;
    
    print qq{        <div class="pagination">\n};
    
    # Previous page link
    if ($current_page > 1) {
        my $prev_page = $current_page - 1;
        print qq{            <a href="?page=$prev_page&sort=$sort_field&order=$sort_order">&larr; Previous</a>\n};
    }
    
    # Page number links
    my $start_page = $current_page > 3 ? $current_page - 2 : 1;
    my $end_page = $start_page + 4;
    $end_page = $total_pages if $end_page > $total_pages;
    $start_page = $end_page - 4 if $end_page - $start_page < 4 && $end_page > 4;
    $start_page = 1 if $start_page < 1;
    
    if ($start_page > 1) {
        print qq{            <a href="?page=1&sort=$sort_field&order=$sort_order">1</a>\n};
        print qq{            <span>...</span>\n} if $start_page > 2;
    }
    
    for my $p ($start_page..$end_page) {
        if ($p == $current_page) {
            print qq{            <span class="current">$p</span>\n};
        } else {
            print qq{            <a href="?page=$p&sort=$sort_field&order=$sort_order">$p</a>\n};
        }
    }
    
    if ($end_page < $total_pages) {
        print qq{            <span>...</span>\n} if $end_page < $total_pages - 1;
        print qq{            <a href="?page=$total_pages&sort=$sort_field&order=$sort_order">$total_pages</a>\n};
    }
    
    # Next page link
    if ($current_page < $total_pages) {
        my $next_page = $current_page + 1;
        print qq{            <a href="?page=$next_page&sort=$sort_field&order=$sort_order">Next &rarr;</a>\n};
    }
    
    print qq{        </div>\n};

}

