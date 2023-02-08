# Document Formatting Helper

An add-on to facilitate knowledge and management of document formatting for blind users.

* Author: Alberto Buffolino;
* Download [development version;][dev]
* NVDA compatibility: probably 2021.1 and beyond.


## What already exists

A formatting viewer, to invoke with NVDA+shift+ctrl+o, that exposes a checkable list of the formatting specific to some parts (that is, non-common), and a refreshable, filtered view over the document content, according to the chosen formatting in previous list.

The checkable list presents the attributes (styles, fonts, colors...) that user can check, and, between brackets, a count of non-consecutive blocks found with the specific attribute.

The default invoking keybinding can be customized in Input gestures dialog.

Pressing enter on a word in filtered view moves the focus back to document, and caret over that word (if you don't modified document in the meantime).

This viewer requires an initial analysis of the document, that can take some time according to page amount. Analysis can be stopped in any time, pressing again the invoking keybinding. A progress announcement is present (beeps and percentage in foreground, beeps only in background); meanwhile, user can do any other activity outside of the document. When finished, the main window popups in foreground.

Unfortunately, at the moment analysis must be run each time you open the formatting viewer (or you want an updated view).

And UIA is not supported (always for the moment).

## What (hopefully) should exist in future

General todo and a list of features that could help in all scenarios (see also [NVDA issue 9527][related-issue]).

* A better code organization to speed-up and support all specific involved technologies (IAccessible, VBA, UIA...).
* a quick navigation among formatted items (bold, italic, colored/with same color...);
* a "go to" feature (without analysis);
* a "go to similar" feature (just the word under the caret is analyzed);
* a "target to" feature (like "go to" but with full document analysis);
* a "eye-catching alert" feature (announcement whether something differs for font size, text or background color... in such way to be very evident to a sighted people).


[dev]: https://github.com/ABuffEr/documentFormattingHelper/releases/download/20230208-dev/documentFormattingHelper-20230208-dev.nvda-addon
[related-issue]: https://github.com/nvaccess/nvda/issues/9527
