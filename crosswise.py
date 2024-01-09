from crossview import CrossView
from argparse import ArgumentParser, SUPPRESS

def parse_cmdline():
    p = ArgumentParser( description='Control a lacrosse WiFi-connected clock without the phone app' )
    p.add_argument('-u', '--user', metavar='USER', help='LaCrosse View username')
    p.add_argument('-p', '--password', metavar='PASS', help='LaCrosse View password')
    p.add_argument('-d', '--device-serial', metavar='AB123C', help='Device serial, for alarm set/show operations')
    return p.parse_args()

def choose( prompt, what, choices ):
    print( prompt.capitalize()+ "s:" )
    for c in choices: print( c )
    print( )
    count = len( what )
    if count == 1: return what[ 0 ]
    index = ''
    while index == '':
        index = input( 'Choose ' + prompt + ': ')
        if index.isnumeric():
            index = int( index )
            if index < 1 or index > count:
                index = ''
        else:
            index = ''
    return what[ index - 1 ]

def get_serial( opts ):
    return opts.device_serial if opts.device_serial else \
        input("Your device serial: ")

def get_ds_id( opts ):
    return input("Data stream identifier: ")

def get_alarm_setting():
    return input("JSON-format alarm data: ")

def msg( s ):
    return '' if s == ':auto' else s

def list( cv, dev ):
    ds = cv.get_data_streams( dev )
    if isinstance( ds, str ):
        print( ds )
        return
    print( f"{'identifier'.ljust(10)} {'enable'.ljust(8)} {'sort key'.ljust(10)} {'message_one'.ljust(20)} {'message_two'.ljust(20)} {'reading'}" )
    print( f"{'------'.ljust(10,'-')} {'-'.ljust(8,'-')} {'----'.ljust(10,'-')} {'-------'.ljust(20,'-')} {'-------'.ljust(20,'-')} {''.ljust(20,'-')}" )
    for card in sorted( ds.get( 'cards' ), key=lambda card: -card['weight'] ) :
        print( f"{str(card['identifier']).ljust(10)} {str(card['enabled?']).ljust(8)} {str(card['weight']).ljust(10)} " + \
               f"{msg(card['message_one']).ljust(20)} {msg(card['message_two']).ljust(20)} {card['reading'] if 'reading' in card else ''}" )

def catalog( cv ):
    n = 0
    for sub in cv.catalog():
        n += 1
        print( f"    {n} - {sub}" )

def help():
    print('Options:')
    #print('    locations       - list locations')
    #print('    location        - choose a location')
    #print('    devices         - list devices for chosen location')
    print('    show            - show alarm')
    print('    set             - set alarm')
    print('    list            - list data streams')
    print('    get             - get single stream')
    print('    add             - add text data stream')
    print('    delete          - delete data stream entry')
    print('    replace         - replace text data stream')
    print('    catalog         - list available weather data stream items')
    print('    subscribe       - add weather data stream')
    print('')
    print("show/set will require your display's device serial#, available from the phone app or printed on your device")
        
def main():
    opts = parse_cmdline()
    if not opts.user or not opts.password:
        print( "user and password are required" )
        return

    cv = CrossView( opts )

    choices = [ f"    {loc.index} - {loc.name}" for loc in cv.locations ]
    loc = choose( 'location', cv.locations, choices )

    devices = cv.get_location_devices( loc )
    choices = [ f"    {d.index} - {d.name} ({d.sensor_type})" for d in devices ]
    dev = choose( 'device', devices, choices )

    print( f"location: {loc.id}, device: {dev.id} sensor: {dev.sensor_id}" )

    miscount = 0
    while True:
        operation = input("> ")
        operation = operation.strip()
        missed = False
        if operation == 'help':
            help()
        elif operation == 'show':
            print( cv.get_alarm( get_serial( opts ) ) )
        elif operation == 'set':
            print( cv.set_alarm( get_serial( opts ), get_alarm_setting() ) )
        elif operation == 'list':
            list( cv, dev )
        elif operation == 'delete':
            print( cv.delete_data_stream( dev, get_ds_id( opts ) ) )
        elif operation == 'get':
            print( cv.get_single_stream( dev, get_ds_id( opts ) ) )
        elif operation == 'add':
            print( cv.add_data_stream( dev, input( "message one: " ), input( "message two: " ) ) )
        elif operation == 'replace':
            print( cv.update_data_stream( dev, get_ds_id( opts ), input( "message one: " ), input( "message two: " ) ) )
        elif operation == 'catalog':
            catalog( cv )
        elif operation == 'subscribe':
            print( cv.subscribe( dev, input( "subscription name or number: " ) ) )
        else:
            missed = True
        if missed:
            miscount += 1
            if miscount == 3:
                print( "Perhaps try 'help'?" )
        elif miscount < 3:
            miscount = 0

if __name__ == "__main__":
    print("Please note: LaCrosse's servers can be quite slow. Timeouts or delays of 10-20s are not uncommon.")
    try:
        main()
    except (EOFError,KeyboardInterrupt):
        pass
