# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from django.core.exceptions import ObjectDoesNotExist
from rides.models import Route, AdSource


class RideSavingPipeline(object):
    def process_item(self, item, spider):
        # Ride needs a PK value before using many-to-many relationship
        item.save()
        # Process raw origin/destination pairs
        for route_dict in item['routes']:
            origin = route_dict['origin']
            destination = route_dict['destination']
            # Get existing route
            try:
                db_route = Route.objects.get(
                    origin=origin,
                    destination=destination)
                item.instance.routes.add(db_route)
            # Or create new one
            except ObjectDoesNotExist:
                item.instance.routes.create(
                    origin=origin,
                    destination=destination)
        # Save item routes
        item.save()
        return item


class SetSourcePipeline(object):
    def process_item(self, item, spider):
        # Get ad source from DB or create new if needed
        try:
            source = AdSource.objects.get(name=spider.name)
        except:
            source = AdSource.objects.create(
                name=spider.name,
                # CAUTION - what if there are multiple urls???
                url=spider.start_urls[0],
                ad_id_pattern=spider.ad_id_pattern)
        item.instance.ad_source = source
        item.save()
        return item
