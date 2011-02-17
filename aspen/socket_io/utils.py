try:
    import json
except ImportError:
    import simplejson as json


frame = '~m~'

def stringify(message):
    if isinstance(message, basestring):
        return message
    else:
        return '~j~' + json.dumps(message)

def encode(messages):
    out = ''
    message = ''
    if isinstance(messages, basestring):
        messages = [messages]
    for message in messages:
        if not message:
            message = ''
        message = stringify(message)
        out += "%s%d%s%s" % (frame, len(message), frame, message)
    return out 

def decode(data):
    messages = []
    while data:
        if (data.substr(0, 3) != frame):
            return messages
        data = data.substr(3)
        number = ''
        n = ''
        for i in range(len(data)):
            n = Number(data.substr(i, 1))
            if (data.substr(i, 1) == n):
                number += n
            else:
                data = data.substr(number.length + frame.length)
                number = Number(number)
                break
        messages.push(data.substr(0, number)); # here
        data = data.substr(number)
    return messages
