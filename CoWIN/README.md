## CoWIN Vax Centers Aggregator, Filter, and Notifier

This utility allows you to fetch CoWIN vax centers in/around Bangalore.
Centers roughly within 3-4 hrs driving distance are covered, and
currently include the districts of BBMP, Bangalore Urban, Bangalore
Rural, Tumkur, Kolar, Ramanagara, Mandya, Mysore, Chamarajanagara,
Chikkaballapura, Chitradurga, Hassan, Dharmapuri, Krishnagiri, and
Chittoor.

You can use the utility in two modes: **fetch** and **notify**

In **fetch** mode, the URL begins with
"https://127.0.0.1:8000/cowin/fetch/..." and is followed by 0 or
more **filters** separated by /

**Filters** allow the listing of results that are relevant to you, and
can be based on pincode, area, district, vaccine type, availability,
age, etc.

For example, "https://127.0.0.1:8000/cowin/fetch/covax/avail/18"
includes filters **covax**, **avail**, and **18**, and will fetch only
centers that are vaccinating people who are 18+ with covax, and which
currently have availibilty. More details of filters with examples is
described in the next section.

You can also register to be notified when there is availibility on your
filtered list, using
"https://127.0.0.1:8000/cowin/notify/email@domain.com/...", where, as
before, the URL is followed by the list of filters. The **avail** filter
is added by default even if not specified (only for notifications).

An email will be sent to the email id provided, (email@domain.com in the
URL above) whenever the list of centers that have availibility in the
filtered list changes.

You can unsubscribe from notifications using the **denotify** command:
"https://127.0.0.1:8000/cowin/denotify/email@domain.com". This will
stop notifications to `email@domain.com`

To change a registered filter, simply re-register with a new filter on
the same email id. The old filter will be replaced by the new one.

### More on filters

In the examples below, replace "fetch" with
"notify/email@domain.com" to register the filter for notification.
Note that the **avail** filter is added by default for notifications

**Fetch all centers**
<https://127.0.0.1:8000/cowin/fetch>

**Filter: covax** - Fetch only covax centers
<https://127.0.0.1:8000/cowin/fetch/covax>

**Filter: covsh** - Fetch only covishield centers
<https://127.0.0.1:8000/cowin/fetch/covsh>

**Filter: avail** - Fetch only centers with availability (Dose 1 or Dose2)
<https://127.0.0.1:8000/cowin/fetch/avail>

**Filter: dose1** - Fetch only centers with Dose 1 availability
<https://127.0.0.1:8000/cowin/fetch/dose1>

**Filter: dose2** - Fetch only centers with Dose 2 availability
<https://127.0.0.1:8000/cowin/fetch/dose2>

**Filter: 18** - Fetch only centers marked 18+
<https://127.0.0.1:8000/cowin/fetch/18>

**Filter: 560003** - Fetch only centers in pincode 560003 (example)
<https://127.0.0.1:8000/cowin/fetch/560003>

**Filters can be cascaded in any order** - they will all be applied
<https://127.0.0.1:8000/cowin/fetch/covax/avail/18>
will fetch all centers where covax is available and marked 18+.

**Order of filter does NOT matter.** So:
<https://127.0.0.1:8000/cowin/fetch/covax/avail/18>
is the same as:
<https://127.0.0.1:8000/cowin/fetch/18/covax/avail>
is the same as:
<https://127.0.0.1:8000/cowin/fetch/covax/18/avail>

**Generic word filter** - Fetch only centers that contain a particular
word, for example, "kolar"
<https://127.0.0.1:8000/cowin/fetch/kolar>
will fetch all centers that contain the word "kolar" in any of its
fields
Uppercase/lowercase does NOT matter - any center that contains kolar,
Kolar, KOLAR, KoLaR will be returned

Can be cascaded with other filters in any order, example:
<https://127.0.0.1:8000/cowin/fetch/covax/kolar/avail/18>

**Word filters can be OR-ed with the | operator**
<https://127.0.0.1:8000/cowin/fetch/covax/bbmp|bangalore|mysore/avail/18>\
will fetch all 18+ covax sites with availability that have Mysore or
Bangalore or BBMP in any field

**E-mail:** [Achyut Bharadwaj](mailto:achyut@acutebar.in)
