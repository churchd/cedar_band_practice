#!/usr/bin/perl
#
# search.cgi - Search Cedar Cross Band practice songs
# Handles search queries from search.html form
# Supports title-only and title+filename search modes
#
# Author: Generated for Cedar Cross Band
# Date: September 2025
# Updated: Novemnber 2025 to revise configuration variables to point to practice directory
#
# test command line:
# # Test specific search bash
#   > echo | QUERY_STRING="query=lord&search_type=title" REQUEST_METHOD=GET perl search.cgi
#  ksh
#   > print | QUERY_STRING="query=lord&search_type=title" REQUEST_METHOD=GET perl search.cgi
#   > print | QUERY_STRING="query=&search_type=title" REQUEST_METHOD=GET perl search.cgi
use strict;
use warnings;
use CGI qw(:standard);
use File::Basename;

# Configuration
my $home_dir = $ENV{HOME} || "/home/churchd";
my $SONGLIST_FILE = "$home_dir/private_html/CedarCrossBand/songlist.txt";
my $MP3_BASE_URL = "../CedarCrossBand/mp3s";
my $CSS_URL = "/~churchd/CedarCrossBand/css/style.css";
my $SONGS_PER_PAGE = 25;

# CGI object
my $cgi = CGI->new;

# Get parameters
my $query = $cgi->param('query') || '';
my $search_type = $cgi->param('search_type') || 'title';
my $page = $cgi->param('page') || 1;
my $sort = $cgi->param('sort') || 'title';
my $order = $cgi->param('order') || 'asc';
my $match_mode = $cgi->param('match_mode') || 'all';

# Validate and clean parameters
$query =~ s/^\s+|\s+$//g;  # Trim whitespace
$search_type = 'title' unless $search_type =~ /^(title|all)$/;
$page = 1 if $page !~ /^\d+$/ || $page < 1;
$sort = 'title' unless $sort =~ /^(title|date|filename)$/;
$order = 'asc' unless $order =~ /^(asc|desc)$/;
$match_mode = 'all' unless $match_mode =~ /^(all|any)$/;

# Read and search song list
my @all_songs = read_songlist();
my @matching_songs = search_songs(\@all_songs, $query, $search_type);
@matching_songs = sort_songs(\@matching_songs, $sort, $order);

# Calculate pagination
my $total_songs = scalar @matching_songs;
my $total_pages = int(($total_songs + $SONGS_PER_PAGE - 1) / $SONGS_PER_PAGE);
$total_pages = 1 if $total_pages == 0;  # At least one page
$page = $total_pages if $page > $total_pages && $total_pages > 0;

my $start_idx = ($page - 1) * $SONGS_PER_PAGE;
my $end_idx = $start_idx + $SONGS_PER_PAGE - 1;
$end_idx = $total_songs - 1 if $end_idx >= $total_songs;

my @page_songs = ();
@page_songs = @matching_songs[$start_idx..$end_idx] if $total_songs > 0;

# Generate HTML
print $cgi->header(-type => 'text/html', -charset => 'utf-8');
print_html_page(\@page_songs, $page, $total_pages, $total_songs, $sort, $order, $query, $search_type);

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
        
        push @songs, {
            filename => $filename,
            title => $title,
            date => $date
        };
    }
    
    close $fh;
    return @songs;
}

sub search_songs {
    my ($songs_ref, $search_query, $search_type) = @_;
    my @matches = ();
    
    # If no query provided, return all songs
    if (!defined $search_query || $search_query eq '') {
        return @$songs_ref;
    }
    
    # Split query into individual terms for multi-word searching
    my @terms = split /\s+/, lc($search_query);
    
    foreach my $song (@$songs_ref) {
        my $match_found = 0;
        
        if ($search_type eq 'title') {
            # Search title only
            my $title_lower = lc($song->{title});
            # delete: $match_found = 1 if all_terms_match($title_lower, \@terms);
	    if ($match_mode eq 'all') {
        	$match_found = 1 if all_terms_match($title_lower, \@terms);
    	    } else {
        	$match_found = 1 if any_term_matches($title_lower, \@terms);
    	    }
        } elsif ($search_type eq 'all') {
            # Search both title and filename
            my $title_lower = lc($song->{title});
            my $filename_lower = lc($song->{filename});
            
            $match_found = 1 if all_terms_match($title_lower, \@terms) || 
                               all_terms_match($filename_lower, \@terms);
        }
        
        push @matches, $song if $match_found;
    }
    
    return @matches;
}


sub all_terms_match {
    my ($text, $terms_ref) = @_;
    
    foreach my $term (@$terms_ref) {
        return 0 unless index($text, $term) >= 0;  # All terms must be present
    }
    
    return 1;  # All terms found
}

sub any_term_matches {
    my ($text, $terms_ref) = @_;
    
    foreach my $term (@$terms_ref) {
        return 1 if index($text, $term) >= 0;  # Any term matches
    }
    
    return 0;  # No terms found
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
    my ($songs_ref, $current_page, $total_pages, $total_songs, $sort_field, $sort_order, $query, $search_type) = @_;
    
    my $safe_query = html_escape($query);
    my $encoded_query = url_encode($query);
    my $encoded_search_type = url_encode($search_type);
    
    # Determine result description
    my $result_desc;
    if ($query eq '') {
        $result_desc = "Showing all $total_songs song(s)";
    } else {
        my $search_desc = $search_type eq 'title' ? "titles" : "titles and filenames";
        $result_desc = "Found $total_songs song(s) matching \"$safe_query\" in $search_desc";
    }
    
    # Determine opposite sort order for toggle links
    my $opposite_order = $sort_order eq 'asc' ? 'desc' : 'asc';
    
    print <<EOF;
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="robots" content="noindex, nofollow">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results - Cedar Cross Band</title>
    <link rel="stylesheet" href="$CSS_URL">
    <style>
        .search-header {
            margin: 20px 0;
            padding: 15px;
            background-color: #f5f5f5;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .search-summary {
            margin-bottom: 15px;
            font-size: 1.1em;
            color: #2c3e50;
        }
        .new-search {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
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
        .no-results {
            text-align: center;
            padding: 40px 20px;
            background: white;
            border-radius: 10px;
            margin: 20px 0;
        }
        .no-results h3 {
            color: #666;
            margin-bottom: 15px;
        }
        .no-results p {
            color: #888;
            margin-bottom: 20px;
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
            <a href="../CedarCrossBand/search.html">New Search</a>
            <a href="browse.cgi">Browse All Songs</a>
            <a href="../CedarCrossBand/about.html">About</a>
        </nav>
        
        <div class="search-header">
            <h2>Search Results</h2>
            <div class="search-summary">
                <strong>$result_desc</strong>
            </div>
EOF

    if ($query ne '') {
        print <<EOF;
            <div class="new-search">
                <a href="../CedarCrossBand/search.html"> Start a new search</a> |
                <a href="?query=&search_type=$search_type">Show all songs</a>
            </div>
EOF
    }

    print <<EOF;
            
            <div class="sort-controls">
                <strong>Sort by:</strong>
EOF

    # Sort control links - include search parameters
    my $title_class = $sort_field eq 'title' ? 'current-sort' : '';
    my $date_class = $sort_field eq 'date' ? 'current-sort' : '';
    my $filename_class = $sort_field eq 'filename' ? 'current-sort' : '';
    
    my $title_order = $sort_field eq 'title' ? $opposite_order : 'asc';
    my $date_order = $sort_field eq 'date' ? $opposite_order : 'desc';
    my $filename_order = $sort_field eq 'filename' ? $opposite_order : 'asc';
    
    print qq{                <a href="?query=$encoded_query&search_type=$encoded_search_type&sort=title&order=$title_order" class="$title_class">Title};
    print " ^" if $sort_field eq 'title' && $sort_order eq 'asc';
    print " v" if $sort_field eq 'title' && $sort_order eq 'desc';
    print "</a>\n";
    
    print qq{                <a href="?query=$encoded_query&search_type=$encoded_search_type&sort=date&order=$date_order" class="$date_class">Date Added};
    print " ^" if $sort_field eq 'date' && $sort_order eq 'asc';
    print " v" if $sort_field eq 'date' && $sort_order eq 'desc';
    print "</a>\n";
    
    print qq{                <a href="?query=$encoded_query&search_type=$encoded_search_type&sort=filename&order=$filename_order" class="$filename_class">Filename};
    print " ^" if $sort_field eq 'filename' && $sort_order eq 'asc';
    print " v" if $sort_field eq 'filename' && $sort_order eq 'desc';
    print "</a>\n";
 
    print <<EOF;
            </div>
        </div>
EOF

    # Pagination controls (top)
    if ($total_pages > 1) {
        print_pagination($current_page, $total_pages, $sort_field, $sort_order, $encoded_query, $encoded_search_type);
    }
    
    # Song list or no results message
    if (@$songs_ref == 0) {
        if ($query eq '') {
            print <<EOF;
        <div class="no-results">
            <h3>No songs in database</h3>
            <p>The song database appears to be empty.</p>
            <p><a href="../CedarCrossBand/">Return to home page</a></p>
        </div>
EOF
        } else {
            print <<EOF;
        <div class="no-results">
            <h3>No songs found</h3>
            <p>No songs matched your search for "<strong>$safe_query</strong>".</p>
            <p>Try:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>Checking your spelling</li>
                <li>Using fewer or different keywords</li>
                <li>Searching in both titles and filenames</li>
                <li><a href="?query=&search_type=$search_type">Browsing all songs</a></li>
            </ul>
            <p style="margin-top: 20px;">
                <a href="../CedarCrossBand/search.html"> Try a new search</a>
            </p>
        </div>
EOF
        }
    } else {
        print qq{        <div class="song-list">\n};
        
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
        
        print qq{        </div>\n};
    }
    
    # Pagination controls (bottom)
    if ($total_pages > 1) {
        print_pagination($current_page, $total_pages, $sort_field, $sort_order, $encoded_query, $encoded_search_type);
    }
    
    print <<EOF;
        
        <footer>
            <p><a href="../CedarCrossBand/">&larr; Back to Home</a> | <a href="../CedarCrossBand/search.html">New Search</a></p>
        </footer>
    </div>
</body>
</html>
EOF
}

sub print_pagination {
    my ($current_page, $total_pages, $sort_field, $sort_order, $encoded_query, $encoded_search_type) = @_;
    
    print qq{        <div class="pagination">\n};
    
    # Previous page link
    if ($current_page > 1) {
        my $prev_page = $current_page - 1;
        print qq{            <a href="?query=$encoded_query&search_type=$encoded_search_type&page=$prev_page&sort=$sort_field&order=$sort_order">&larr; Previous</a>\n};
    }
    
    # Page number links
    my $start_page = $current_page > 3 ? $current_page - 2 : 1;
    my $end_page = $start_page + 4;
    $end_page = $total_pages if $end_page > $total_pages;
    $start_page = $end_page - 4 if $end_page - $start_page < 4 && $end_page > 4;
    $start_page = 1 if $start_page < 1;
    
    if ($start_page > 1) {
        print qq{            <a href="?query=$encoded_query&search_type=$encoded_search_type&page=1&sort=$sort_field&order=$sort_order">1</a>\n};
        print qq{            <span>...</span>\n} if $start_page > 2;
    }
    
    for my $p ($start_page..$end_page) {
        if ($p == $current_page) {
            print qq{            <span class="current">$p</span>\n};
        } else {
            print qq{            <a href="?query=$encoded_query&search_type=$encoded_search_type&page=$p&sort=$sort_field&order=$sort_order">$p</a>\n};
        }
    }
    
    if ($end_page < $total_pages) {
        print qq{            <span>...</span>\n} if $end_page < $total_pages - 1;
        print qq{            <a href="?query=$encoded_query&search_type=$encoded_search_type&page=$total_pages&sort=$sort_field&order=$sort_order">$total_pages</a>\n};
    }
    
    # Next page link
    if ($current_page < $total_pages) {
        my $next_page = $current_page + 1;
        print qq{            <a href="?query=$encoded_query&search_type=$encoded_search_type&page=$next_page&sort=$sort_field&order=$sort_order">Next &rarr;</a>\n};
    }
    
    print qq{        </div>\n};
}
