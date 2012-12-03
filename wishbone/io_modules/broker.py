#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  broker.py
#  
#  Copyright 2012 Jelle Smet development@smetj.net
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import logging
from wishbone.toolkit import QueueFunctions, Block
from gevent import Greenlet, spawn, sleep
from gevent.queue import Queue
from amqplib import client_0_8 as amqp
from gevent import monkey;monkey.patch_all()

class Broker(Greenlet, QueueFunctions, Block):
    '''**A Wisbone IOmodule which handles AMQP0.8 input and output.  It's meant to be
    resillient to disconnects and broker unavailability.**
    
    Data consumed from the broker goes into self.inbox
    Data which should be produced towards to broker goes into self.outbox
    
    Acknowledging:
    
    Messages which arrive in the outbox and which have an acknowledge tag in the header will be acknowledged.
    When a broker_tag is submitted to the acknowledge queue the tag is acknowledged with the broker.
    
    The message submitted to self.outbox should have 3 values in its headers:
    
        {'header':{'broker_exchange':name, 'broker_key':name, 'broker_tag':tag}}
        
        * broker_exchange:    The exchange to which data should be submitted.
        * broker_key:         The routing key used when submitting data.
        * broker_tag:         The tag used to acknowledge the message from the broker.
        
        Queues:
        
        * inbox:              The queue containing messages coming from the broker.
        * outbox:             The queue containing messages to the broker.
        * acknowledge:        The queue containing messages to acknowledge

        Parameters:

        * name:               The name you want this module to be registered under.
        * host:               The name or IP of the broker.
        * vhost:              The virtual host of the broker. By default this is '/'.
        * username:           The username to connect to the broker.  By default this is 'guest'.
        * password:           The password to connect to the broker.  By default this is 'guest'.
        * consume_queue:      The queue which should be consumed. By default this is "wishbone_in".
        * prefetch_count:     The amount of messages consumed from the queue at once.
        * no_ack:             No acknowledgements required? By default this is False (means acknowledgements are required.)
        * delivery_mode       The message delivery mode.  1 is Non-persistent, 2 is Persistent. Default=2
    '''
    
    def __init__(self, name, host, vhost='/', username='guest', password='guest', prefetch_count=1, no_ack=False, consume_queue='wishbone_in', delivery_mode=2 ):
    
        Greenlet.__init__(self)
        Block.__init__(self)
        QueueFunctions.__init__(self)
        self.name=name
        self.logging = logging.getLogger( self.name )
        self.logging.info('Initiated')
        self.host=host
        self.vhost=vhost
        self.username=username
        self.password=password
        self.prefetch_count=prefetch_count
        self.no_ack=no_ack
        self.consume_queue = consume_queue
        self.delivery_mode=delivery_mode
        self.createQueue("acknowledge")
        self.connected=False

    def __setup(self):
        '''Handles connection and channel creation.
        '''
        
        self.conn = amqp.Connection(host="%s:5672"%(self.host), userid=self.username,password=self.password, virtual_host=self.vhost, insist=False)
        self.incoming = self.conn.channel()
        self.incoming.basic_qos(prefetch_size=0, prefetch_count=self.prefetch_count, a_global=False)
        self.outgoing = self.conn.channel()
        self.logging.info('Connected to broker')
        
    def submitBroker(self):
        '''Submits all data from self.outbox into the broker by calling the produce() funtion.
        '''
        
        while self.block() == True:
            while self.connected == True:
                try:
                    self.produce(self.getData("outbox"))
                except Exception as err:
                    self.logging.warn('Could not write data to broker.  Reason: %s'%(err))
                    break
            self.wait(timeout=0.1)    
    
    def acknowledgeMessage(self):
        '''Acknowledges messages
        '''       
        
        while self.block() == True:
            while self.connected == True:
                try:
                    ack = self.getData("acknowledge")
                    self.incoming.basic_ack(ack)
                except Exception as err:
                    self.putData(ack,"acknowledge")
                    self.logging.warn('Could not acknowledge message in broker.  Reason: %s'%(err))
                    break
            self.wait(timeout=0.1)
                                
    def _run(self):
        '''
        Blocking function which start consumption and producing of data.  It is executed when issuing the Greenlet start()
        '''
        
        self.logging.info('Started')
        night=0.5
        outgoing = spawn ( self.submitBroker )        
        acknowledging = spawn ( self.acknowledgeMessage )        
        while self.block() == True:
            while self.connected==False and self.block() == True:
                try:
                    if night < 512:
                        night *=2
                    self.__setup()
                    self.connected = True
                    self.incoming.basic_consume(queue=self.consume_queue, callback=self.consume, consumer_tag='request', no_ack=self.no_ack)
                    night=0.5
                except Exception as err:
                    self.connected=False
                    self.logging.error('Connection to broker lost. Reason: %s. Try again in %s seconds.' % (err,night) )
                    self.wait(night)
            self.logging.info('Connected')
            while self.block() == True and self.connected == True:                
                try:
                    self.incoming.wait()
                except Exception as err:
                    self.logging.error('Connection to broker lost. Reason: %s' % err )
                    self.connected = False
                    try:
                        self.incoming.close()
                    except:
                        pass
                    try:
                        self.conn.close()
                    except:
                        pass
                    break                   
        
    def consume(self,doc):
        '''Is called upon each message coming from the broker infrastructure.
        
        It also makes sure the incoming data is encapsulated in the right Wishbone format.
        When successful, this function acknowledges the message from the broker.
        '''
        self.putData({'header':{'broker_tag':doc.delivery_tag},'data':doc.body}, queue='inbox')
        self.logging.debug('Data received from broker.')
         
    def produce(self,message):
        '''Is called upon each message going to to the broker infrastructure.
        
        This function is called by the consume() function.  If the correct header info isn't present (but that would be odd at this point), the data is purged.
        '''

        if message["header"].has_key('broker_exchange') and message["header"].has_key('broker_key'):            
            if self.connected == True:
                msg = amqp.Message(str(message['data']))
                msg.properties["delivery_mode"] = self.delivery_mode
                self.outgoing.basic_publish(msg,exchange=message['header']['broker_exchange'],routing_key=message['header']['broker_key'])
                if message['header'].has_key('broker_tag') and self.no_ack == False:
                    self.incoming.basic_ack(message['header']['broker_tag'])
            else:
                raise Exception('Not Connected to broker')
        else:
            self.logging.warn('Received data for broker without exchange or key information in header. Purged.')
            if message['header'].has_key('broker_tag') and self.no_ack == False:
                self.incoming.basic_ack(message['header']['broker_tag'])

    def shutdown(self):
        '''This function is called on shutdown().'''
        
        try:
             self.incoming.basic_cancel('request')
        except:
            pass
        self.logging.info('Shutdown')
